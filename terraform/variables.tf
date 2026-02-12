variable "project_id" {
  description = "The Google Cloud project ID"
  type        = string
}

variable "region" {
  description = "The region to deploy resources in"
  type        = string
  default     = "us-central1"
}

variable "bucket_name" {
  description = "The name of the GCS bucket for document uploads"
  type        = string
}

variable "dataset_id" {
  description = "The BigQuery dataset ID"
  type        = string
  default     = "document_processing"
}

variable "table_id" {
  description = "The BigQuery table ID"
  type        = string
  default     = "processed_documents"
}
