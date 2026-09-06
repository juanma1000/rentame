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

# One-off ECS cluster to host the monthly Pago-generation job. Reuse an
# existing cluster via a `cluster_arn` variable instead if the backend's
# App Runner setup already shares infra with an ECS cluster elsewhere —
# same caveat already documented in `infra/aws/migrations-task/main.tf`.
resource "aws_ecs_cluster" "pagos_mensuales" {
  name = "rentame-${var.environment}-pagos-mensuales"
}

resource "aws_cloudwatch_log_group" "pagos_mensuales" {
  name              = "/ecs/rentame-${var.environment}-pagos-mensuales"
  retention_in_days = 14
}

# Task execution role: lets ECS pull the image from ECR and write logs.
resource "aws_iam_role" "execution" {
  name = "rentame-${var.environment}-pagos-mensuales-exec"

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

# Task role: permissions the running container itself needs. This job
# only touches the DB (via DATABASE_URL) and, once Wompi credentials are
# configured (task 8.3's WOMPI_API_KEY env var, out of scope for this
# variables.tf — added alongside the real Wompi rollout per design.md's
# Migration Plan step 3), reaches Wompi's public HTTPS API — no extra AWS
# permissions required beyond what's granted through the execution role's
# secret read above.
resource "aws_iam_role" "task" {
  name = "rentame-${var.environment}-pagos-mensuales-task"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
    }]
  })
}

resource "aws_ecs_task_definition" "generar_pagos_mensuales" {
  family                   = "rentame-${var.environment}-pagos-mensuales"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.cpu
  memory                   = var.memory
  execution_role_arn       = aws_iam_role.execution.arn
  task_role_arn            = aws_iam_role.task.arn

  container_definitions = jsonencode([{
    name    = "generar-pagos-mensuales"
    image   = "${var.ecr_repository_url}:latest" # overridden per-run by the CI workflow (--overrides)
    command = ["python", "scripts/generar_pagos_mensuales.py"]
    environment = [
      { name = "RUN_MIGRATIONS", value = "false" }, # entrypoint must not also self-migrate
      { name = "PYTHONPATH", value = "/app" }       # python prepends the script's own dir
      # (/app/scripts) to sys.path, not /app — without this, `import pagos` 404s with
      # ModuleNotFoundError. WORKDIR is /app (see backend/Dockerfile).
    ]
    secrets = [
      { name = "DATABASE_URL", valueFrom = var.database_url_secret_arn }
    ]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.pagos_mensuales.name
        "awslogs-region"        = var.region
        "awslogs-stream-prefix" = "pagos-mensuales"
      }
    }
  }])
}

# Security group for the job task: no inbound needed, only outbound to
# RDS on 5432 and HTTPS for ECR/Secrets Manager/CloudWatch/Wompi.
resource "aws_security_group" "pagos_mensuales" {
  name        = "rentame-${var.environment}-pagos-mensuales"
  description = "Pagos mensuales job task: outbound to RDS and AWS/Wompi APIs only"
  vpc_id      = data.aws_subnet.first_private.vpc_id

  egress {
    description = "Postgres to RDS"
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # narrowed to the RDS SG via the rule below instead
  }

  egress {
    description = "HTTPS for ECR/Secrets Manager/CloudWatch Logs/Wompi"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

data "aws_subnet" "first_private" {
  id = var.vpc_private_subnet_ids[0]
}

# Authorize the job task's SG on the RDS SG's inbound rules, rather than
# opening RDS to 0.0.0.0/0 — this is the actual access grant; the broad
# egress cidr_blocks above is intentionally permissive since egress is
# restricted by security-group-to-security-group ingress on the RDS side.
resource "aws_security_group_rule" "rds_allow_pagos_mensuales" {
  type                     = "ingress"
  from_port                = 5432
  to_port                  = 5432
  protocol                 = "tcp"
  security_group_id        = var.rds_security_group_id
  source_security_group_id = aws_security_group.pagos_mensuales.id
  description              = "Allow pagos mensuales job task to reach RDS"
}

# EventBridge Scheduler role: lets the scheduler run the ECS task on our
# behalf (`ecs:RunTask`) and pass the task/execution roles to ECS
# (`iam:PassRole`) — the piece the one-off migrations task never needed,
# since that one is triggered by CI, not by a recurring schedule.
resource "aws_iam_role" "scheduler" {
  name = "rentame-${var.environment}-pagos-mensuales-scheduler"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "scheduler.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "scheduler_run_task" {
  name = "run-pagos-mensuales-task"
  role = aws_iam_role.scheduler.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["ecs:RunTask"]
        Resource = [aws_ecs_task_definition.generar_pagos_mensuales.arn]
      },
      {
        Effect    = "Allow"
        Action    = ["iam:PassRole"]
        Resource  = [aws_iam_role.execution.arn, aws_iam_role.task.arn]
        Condition = { StringLike = { "iam:PassedToService" = "ecs-tasks.amazonaws.com" } }
      }
    ]
  })
}

# EventBridge Scheduler: fires `var.schedule_expression` (default: once a
# month) and runs `generar_pagos_del_ciclo` via the ECS task above.
# Idempotency lives in the application layer
# (`pagos.application.generar_pagos_del_ciclo`), not here — a missed or
# double-fired schedule invocation is safe by construction (task 9.2's
# integration test), so this schedule needs no additional dedup/locking.
resource "aws_scheduler_schedule" "generar_pagos_mensuales" {
  name       = "rentame-${var.environment}-generar-pagos-mensuales"
  group_name = "default"

  flexible_time_window {
    mode = "OFF"
  }

  schedule_expression = var.schedule_expression

  target {
    arn      = aws_ecs_cluster.pagos_mensuales.arn
    role_arn = aws_iam_role.scheduler.arn

    ecs_parameters {
      task_definition_arn = aws_ecs_task_definition.generar_pagos_mensuales.arn
      launch_type         = "FARGATE"

      network_configuration {
        subnets          = var.vpc_private_subnet_ids
        security_groups  = [aws_security_group.pagos_mensuales.id]
        assign_public_ip = false
      }
    }
  }
}

output "cluster_arn" {
  value = aws_ecs_cluster.pagos_mensuales.arn
}

output "task_definition_arn" {
  value = aws_ecs_task_definition.generar_pagos_mensuales.arn
}

output "schedule_arn" {
  value = aws_scheduler_schedule.generar_pagos_mensuales.arn
}

output "subnet_ids" {
  value = var.vpc_private_subnet_ids
}

output "security_group_id" {
  value = aws_security_group.pagos_mensuales.id
}
