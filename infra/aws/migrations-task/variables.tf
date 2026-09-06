variable "region" {
  description = "AWS region"
  type        = string
}

variable "environment" {
  description = "Deploy environment name, used for resource naming"
  type        = string
  default     = "production"
}

variable "ecr_repository_url" {
  description = "ECR repository URL for the backend image (e.g. 123456789.dkr.ecr.us-east-1.amazonaws.com/rentame-backend)"
  type        = string
}

variable "vpc_private_subnet_ids" {
  description = "Private subnet IDs where the migration task runs (must reach RDS)"
  type        = list(string)
}

variable "rds_security_group_id" {
  description = "Security group attached to the RDS instance, so the migration task's SG can be authorized to reach it on 5432"
  type        = string
}

variable "database_url_secret_arn" {
  description = "Secrets Manager ARN holding DATABASE_URL for the backend/migrations"
  type        = string
}

variable "cpu" {
  description = "Fargate task CPU units"
  type        = string
  default     = "256"
}

variable "memory" {
  description = "Fargate task memory (MiB)"
  type        = string
  default     = "512"
}
