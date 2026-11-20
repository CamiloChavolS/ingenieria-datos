resource "google_project_service" "required" {
  for_each = toset([
    "bigquery.googleapis.com",
    "bigquerydatapolicy.googleapis.com",
    "datacatalog.googleapis.com",
    "aiplatform.googleapis.com",
    "run.googleapis.com",
    "artifactregistry.googleapis.com",
    "cloudbuild.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "iam.googleapis.com",
    "iamcredentials.googleapis.com",
    "sts.googleapis.com",
    "storage.googleapis.com",
  ])
  project            = var.project_id
  service            = each.key
  disable_on_destroy = false
}

resource "google_service_account" "pipeline" {
  account_id   = "ravenstack-pipeline"
  display_name = "RavenStack data and Vertex pipeline"
  project      = var.project_id
  depends_on   = [google_project_service.required]
}

resource "google_service_account" "deploy" {
  account_id   = "ravenstack-deployer"
  display_name = "RavenStack GitLab deployment"
  project      = var.project_id
  depends_on   = [google_project_service.required]
}

resource "google_service_account" "runtime" {
  account_id   = "ravenstack-runtime"
  display_name = "RavenStack Cloud Run runtime"
  project      = var.project_id
  depends_on   = [google_project_service.required]
}

locals {
  pipeline_member = "serviceAccount:${google_service_account.pipeline.email}"
  deploy_member   = "serviceAccount:${google_service_account.deploy.email}"
  runtime_member  = "serviceAccount:${google_service_account.runtime.email}"
}

resource "google_bigquery_dataset" "bronze" {
  dataset_id                 = "bronze"
  location                   = var.bq_location
  delete_contents_on_destroy = false
  depends_on                 = [google_project_service.required]
}

resource "google_bigquery_dataset" "silver" {
  dataset_id                 = "silver"
  location                   = var.bq_location
  delete_contents_on_destroy = false
  depends_on                 = [google_project_service.required]
}

resource "google_bigquery_dataset" "gold" {
  dataset_id                 = "gold"
  location                   = var.bq_location
  delete_contents_on_destroy = false
  depends_on                 = [google_project_service.required]
}

resource "google_project_iam_member" "runtime_jobs" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = local.runtime_member
}

resource "google_project_iam_member" "pipeline_jobs" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = local.pipeline_member
}

resource "google_bigquery_dataset_iam_member" "app_gold_reader" {
  project    = var.project_id
  dataset_id = google_bigquery_dataset.gold.dataset_id
  role       = "roles/bigquery.dataViewer"
  member     = local.runtime_member
}

resource "google_bigquery_dataset_iam_member" "analyst_gold_reader" {
  project    = var.project_id
  dataset_id = google_bigquery_dataset.gold.dataset_id
  role       = "roles/bigquery.dataViewer"
  member     = "group:${var.data_analyst_group}"
}

resource "google_project_iam_member" "analyst_jobs" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "group:${var.data_analyst_group}"
}

resource "google_bigquery_dataset_iam_member" "pipeline_bronze_writer" {
  project    = var.project_id
  dataset_id = google_bigquery_dataset.bronze.dataset_id
  role       = "roles/bigquery.dataEditor"
  member     = local.pipeline_member
}

resource "google_bigquery_dataset_iam_member" "pipeline_silver_writer" {
  project    = var.project_id
  dataset_id = google_bigquery_dataset.silver.dataset_id
  role       = "roles/bigquery.dataEditor"
  member     = local.pipeline_member
}

resource "google_project_iam_member" "pipeline_bigquery_job_user" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = local.pipeline_member
}

resource "google_bigquery_dataset_iam_member" "pipeline_gold_owner" {
  project    = var.project_id
  dataset_id = google_bigquery_dataset.gold.dataset_id
  role       = "roles/bigquery.dataOwner"
  member     = local.pipeline_member
}

resource "google_storage_bucket" "model_artifacts" {
  name                        = "${var.project_id}-ravenstack-models"
  location                    = var.bq_location
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
  force_destroy               = false
}

resource "google_storage_bucket_iam_member" "runtime_model_reader" {
  bucket = google_storage_bucket.model_artifacts.name
  role   = "roles/storage.objectViewer"
  member = local.runtime_member
}

resource "google_storage_bucket_iam_member" "pipeline_model_writer" {
  bucket = google_storage_bucket.model_artifacts.name
  role   = "roles/storage.objectCreator"
  member = local.pipeline_member
}

resource "google_artifact_registry_repository" "app" {
  location      = var.region
  repository_id = "ravenstack"
  format        = "DOCKER"
  depends_on    = [google_project_service.required]
}

resource "google_artifact_registry_repository_iam_member" "gitlab_writer" {
  location   = google_artifact_registry_repository.app.location
  repository = google_artifact_registry_repository.app.name
  role       = "roles/artifactregistry.writer"
  member     = local.deploy_member
}

resource "google_project_iam_member" "pipeline_vertex_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = local.pipeline_member
}

resource "google_data_catalog_taxonomy" "sensitive" {
  region                 = var.data_catalog_region
  display_name           = "RavenStack Restricted Data"
  description            = "Sensitive account-level fields used for governed analytics."
  activated_policy_types = ["FINE_GRAINED_ACCESS_CONTROL"]
  depends_on             = [google_project_service.required]
}

resource "google_data_catalog_policy_tag" "account_identifier" {
  taxonomy     = google_data_catalog_taxonomy.sensitive.id
  display_name = "Customer Identifiers"
  description  = "Account identifiers and names; grant only when the analysis requires them."
}

resource "google_data_catalog_policy_tag_iam_member" "pipeline_fine_grained_reader" {
  policy_tag = google_data_catalog_policy_tag.account_identifier.name
  role       = "roles/datacatalog.categoryFineGrainedReader"
  member     = "serviceAccount:${google_service_account.pipeline.email}"
}

resource "google_iam_workload_identity_pool" "gitlab" {
  workload_identity_pool_id = "gitlab-ravenstack"
  display_name              = "GitLab RavenStack CI"
  description               = "Federated identities for the RavenStack GitLab project."
  depends_on                = [google_project_service.required]
}

resource "google_iam_workload_identity_pool_provider" "gitlab" {
  workload_identity_pool_id          = google_iam_workload_identity_pool.gitlab.workload_identity_pool_id
  workload_identity_pool_provider_id = "gitlab-com"
  display_name                       = "GitLab.com OIDC"
  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.project_path" = "assertion.project_path"
    "attribute.ref"          = "assertion.ref"
  }
  attribute_condition = "assertion.project_path == '${var.gitlab_project_path}' && assertion.ref == '${var.gitlab_protected_ref}' && assertion.ref_protected == true"
  oidc {
    issuer_uri = "https://gitlab.com"
  }
}

resource "google_service_account_iam_member" "gitlab_impersonation" {
  service_account_id = google_service_account.deploy.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.gitlab.name}/attribute.project_path/${var.gitlab_project_path}"
}

resource "google_service_account_iam_member" "gitlab_pipeline_impersonation" {
  service_account_id = google_service_account.pipeline.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.gitlab.name}/attribute.project_path/${var.gitlab_project_path}"
}

resource "google_project_iam_member" "gitlab_cloud_run_admin" {
  project = var.project_id
  role    = "roles/run.admin"
  member  = local.deploy_member
}

resource "google_project_iam_member" "gitlab_cloud_build_builder" {
  project = var.project_id
  role    = "roles/cloudbuild.builds.editor"
  member  = local.deploy_member
}

resource "google_service_account_iam_member" "gitlab_runtime_act_as" {
  service_account_id = google_service_account.runtime.name
  role               = "roles/iam.serviceAccountUser"
  member             = local.deploy_member
}
