output "bucket_url" {
  value = google_storage_bucket.input_bucket.url
}

output "api_url" {
  value = google_cloud_run_v2_service.api_service.uri
}

output "frontend_url" {
  value = google_cloud_run_v2_service.frontend_service.uri
}

output "function_name" {
  value = google_cloudfunctions2_function.gcs_trigger.name
}

output "bq_table" {
  value = "${var.project_id}.${var.dataset_id}.${var.table_id}"
}
