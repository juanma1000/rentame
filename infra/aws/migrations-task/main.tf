terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.region
}

# One-off ECS cluster to host the migration task. Reuse an existing cluster
# via a `cluster_arn` variable instead if the backend's App Runner setup
# already shares infra with an ECS cluster elsewhere.
resource "aws_ecs_cluster" "migrations" {
  name = "rentame-${var.environment}-migrations"
}

resource "aws_cloudwatch_log_group" "migrations" {
  name              = "/ecs/rentame-${var.environment}-migrate"
  retention_in_days = 14
}

# Task execution role: lets ECS pull the image from ECR and write logs.
resource "aws_iam_role" "execution" {
  name = "rentame-${var.environment}-migrate-exec"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "execution_managed" {
  role       = aws_iam_role.execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# Execution role also needs read access to the DATABASE_URL secret, since
# it's what ECS uses to inject secrets into the container at launch.
resource "aws_iam_role_policy" "execution_secrets" {
  name = "read-database-url-secret"
  role = aws_iam_role.execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["secretsmanager:GetSecretValue"]
      Resource = [var.database_url_secret_arn]
    }]
  })
}

# Task role: permissions the running container itself needs. Migrations
# only touch the DB (via DATABASE_URL), so no extra permissions required
# beyond what's granted through the execution role's secret read above.
resource "aws_iam_role" "task" {
  name = "rentame-${var.environment}-migrate-task"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
    }]
  })
}

resource "aws_ecs_task_definition" "migrate" {
  family                   = "rentame-${var.environment}-migrate"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.cpu
  memory                   = var.memory
  execution_role_arn       = aws_iam_role.execution.arn
  task_role_arn            = aws_iam_role.task.arn

  container_definitions = jsonencode([{
    name  = "migrate"
    image = "${var.ecr_repository_url}:latest" # overridden per-run by the CI workflow (--overrides)
    command = ["alembic", "upgrade", "head"]
    environment = [
      { name = "RUN_MIGRATIONS", value = "false" } # entrypoint must not also self-migrate
    ]
    secrets = [
      { name = "DATABASE_URL", valueFrom = var.database_url_secret_arn }
    ]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.migrations.name
        "awslogs-region"        = var.region
        "awslogs-stream-prefix" = "migrate"
      }
    }
  }])
}

# Security group for the migration task: no inbound needed, only outbound
# to RDS on 5432 (and HTTPS for ECR/Secrets Manager/CloudWatch endpoints).
resource "aws_security_group" "migrate" {
  name        = "rentame-${var.environment}-migrate"
  description = "Migration task: outbound to RDS and AWS APIs only"
  vpc_id      = data.aws_subnet.first_private.vpc_id

  egress {
    description = "Postgres to RDS"
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # narrowed to the RDS SG via the rule below instead
  }

  egress {
    description = "HTTPS for ECR/Secrets Manager/CloudWatch Logs"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

data "aws_subnet" "first_private" {
  id = var.vpc_private_subnet_ids[0]
}

# Authorize the migration task's SG on the RDS SG's inbound rules, rather
# than opening RDS to 0.0.0.0/0 — this is the actual access grant; the
# broad egress cidr_blocks above is intentionally permissive since egress
# is restricted by security-group-to-security-group ingress on the RDS side.
resource "aws_security_group_rule" "rds_allow_migrate" {
  type                     = "ingress"
  from_port                = 5432
  to_port                  = 5432
  protocol                 = "tcp"
  security_group_id        = var.rds_security_group_id
  source_security_group_id = aws_security_group.migrate.id
  description              = "Allow migration task to reach RDS"
}

output "cluster_arn" {
  value = aws_ecs_cluster.migrations.arn
}

output "task_definition_arn" {
  value = aws_ecs_task_definition.migrate.arn
}

output "subnet_ids" {
  value = var.vpc_private_subnet_ids
}

output "security_group_id" {
  value = aws_security_group.migrate.id
}
