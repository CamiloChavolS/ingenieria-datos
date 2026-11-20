variable "project_id" {
  type = string
}
variable "region" {
  type    = string
  default = "us-central1"
}
variable "bq_location" {
  type    = string
  default = "US"
}
variable "data_analyst_group" {
  type        = string
  description = "Google group authorized to query governed marts"
}
variable "data_catalog_region" {
  type    = string
  default = "us"
}
variable "gitlab_project_path" {
  type        = string
  description = "Full GitLab path, e.g. group/subgroup/project"
  default     = "replace-me/group/project"
}
variable "gitlab_protected_ref" {
  type        = string
  description = "Protected default branch allowed to impersonate the deploy identity"
  default     = "main"
}
