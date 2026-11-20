output "bigquery_datasets" {
  value = [google_bigquery_dataset.bronze.dataset_id, google_bigquery_dataset.silver.dataset_id, google_bigquery_dataset.gold.dataset_id]
}

output "customer_identifiers_policy_tag" {
  value = google_data_catalog_policy_tag.account_identifier.name
}

output "gitlab_wif_pool" {
  value = google_iam_workload_identity_pool.gitlab.workload_identity_pool_id
}

output "gitlab_wif_provider" {
  value = google_iam_workload_identity_pool_provider.gitlab.workload_identity_pool_provider_id
}

output "project_number" {
  value = data.google_project.current.number
}

output "model_bucket" {
  value = google_storage_bucket.model_artifacts.name
}

output "pipeline_service_account_email" {
  value = google_service_account.pipeline.email
}

output "deploy_service_account_email" {
  value = google_service_account.deploy.email
}

output "runtime_service_account_email" {
  value = google_service_account.runtime.email
}
