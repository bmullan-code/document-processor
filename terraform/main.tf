provider "google" {
  project = var.project_id
  region  = var.region
}

# GCS Bucket for document uploads
resource "google_storage_bucket" "input_bucket" {
  name     = var.bucket_name
  location = var.region
  force_destroy = true

  uniform_bucket_level_access = true
}

# BigQuery Dataset
resource "google_bigquery_dataset" "dataset" {
  dataset_id                  = var.dataset_id
  location                    = var.region
  delete_contents_on_destroy = true
}

# BigQuery Table
resource "google_bigquery_table" "table" {
  dataset_id = google_bigquery_dataset.dataset.dataset_id
  table_id   = var.table_id
  deletion_protection = false

  schema = <<EOF
[
  {
    "name": "document_name",
    "type": "STRING",
    "mode": "REQUIRED"
  },
  {
    "name": "document_size",
    "type": "INTEGER",
    "mode": "REQUIRED"
  },
  {
    "name": "document_type",
    "type": "STRING",
    "mode": "NULLABLE"
  },
  {
    "name": "processed_at",
    "type": "TIMESTAMP",
    "mode": "REQUIRED"
  },
  {
    "name": "extracted_data",
    "type": "JSON",
    "mode": "NULLABLE"
  },
  {
    "name": "error_message",
    "type": "STRING",
    "mode": "NULLABLE"
  },
  {
    "name": "gcs_uri",
    "type": "STRING",
    "mode": "REQUIRED"
  }
]
EOF
}

# Service Account for Cloud Run/Function
resource "google_service_account" "service_account" {
  account_id   = "doc-processor-sa"
  display_name = "Document Processor Service Account"
}

# IAM permissions for BigQuery
resource "google_project_iam_member" "bq_owner" {
  project = var.project_id
  role    = "roles/bigquery.dataEditor"
  member  = "serviceAccount:${google_service_account.service_account.email}"
}

# IAM permissions for Vertex AI
resource "google_project_iam_member" "vertex_ai_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.service_account.email}"
}

# IAM permissions for GCS
resource "google_storage_bucket_iam_member" "bucket_viewer" {
  bucket = google_storage_bucket.input_bucket.name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${google_service_account.service_account.email}"
}

# Cloud Run Service (simplified - assumes image is pushed)
resource "google_cloud_run_v2_service" "api_service" {
  name     = "doc-processor-api"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.service_account.email
    containers {
      image = "gcr.io/${var.project_id}/doc-processor-api:latest"
      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }
      env {
        name  = "BQ_DATASET_ID"
        value = var.dataset_id
      }
      env {
        name  = "BQ_TABLE_ID"
        value = var.table_id
      }
    }
  }
}

# Allow internal traffic to Cloud Run
resource "google_cloud_run_v2_service_iam_member" "api_invoker" {
  location = google_cloud_run_v2_service.api_service.location
  name     = google_cloud_run_v2_service.api_service.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.service_account.email}"
}

# Source code zip for Cloud Function
data "archive_file" "cf_source" {
  type        = "zip"
  output_path = "${path.module}/cf_source.zip"
  source_dir  = "../cloud_function"
}

# Upload source to bucket
resource "google_storage_bucket_object" "cf_code" {
  name   = "cloud_function_source_${data.archive_file.cf_source.output_md5}.zip"
  bucket = google_storage_bucket.input_bucket.name
  source = data.archive_file.cf_source.output_path
}

# Cloud Function
resource "google_cloudfunctions2_function" "gcs_trigger" {
  name        = "process-gcs-upload"
  location    = var.region
  description = "Trigger document processing on GCS upload"

  build_config {
    runtime     = "python310"
    entry_point = "process_gcs_upload"
    source {
      storage_source {
        bucket = google_storage_bucket.input_bucket.name
        object = google_storage_bucket_object.cf_code.name
      }
    }
  }

  service_config {
    max_instance_count = 10
    available_memory   = "256Mi"
    timeout_seconds    = 60
    service_account_email = google_service_account.service_account.email
    environment_variables = {
      API_URL = google_cloud_run_v2_service.api_service.uri
    }
  }

  event_trigger {
    trigger_region = var.region
    event_type     = "google.cloud.storage.object.v1.finalized"
    retry_policy   = "RETRY_POLICY_DO_NOT_RETRY"
    event_filters {
      attribute = "bucket"
      value     = google_storage_bucket.input_bucket.name
    }
  }
}
