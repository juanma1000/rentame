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
  description = "Private subnet IDs where the job task runs (must reach RDS)"
  type        = list(string)
}

variable "rds_security_group_id" {
  description = "Security group attached to the RDS instance, so the job task's SG can be authorized to reach it on 5432"
  type        = string
}

variable "database_url_secret_arn" {
  description = "Secrets Manager ARN holding DATABASE_URL for the backend/job"
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

variable "schedule_expression" {
  description = <<-EOT
    EventBridge schedule expression that triggers the monthly Pago
    generation task. Default fires at 06:00 UTC on the 1st of every
    month — design.md's open question on the exact billing cycle
    duration is deliberately left to `generar_pagos_del_ciclo`'s own
    `DIAS_PLAZO_PAGO` grace period (application-level), not to this
    schedule's cadence; the job itself is idempotent (task 3's
    "no genera un segundo Pago pendiente"), so an operator can safely
    change this cadence (e.g. to run more often as a safety net) without
    risking duplicate Pagos.
  EOT
  type        = string
  default     = "cron(0 6 1 * ? *)"
}
