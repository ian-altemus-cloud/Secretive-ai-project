terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "5.81.0"
    }
  }
}
resource "aws_iam_role" "observability_execution_role" {
  name = "${var.project_name}-${var.environment}-observability-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })

  tags = {
    Name        = "${var.project_name}-${var.environment}-observability-execution-role"
    Environment = var.environment
    Project     = var.project_name
  }
}

resource "aws_iam_role_policy_attachment" "observability_execution_role_policy" {
  role       = aws_iam_role.observability_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role" "observability_task_role" {
  name = "${var.project_name}-${var.environment}-observability-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })

  tags = {
    Name        = "${var.project_name}-${var.environment}-observability-task-role"
    Environment = var.environment
    Project     = var.project_name
  }
}
resource "aws_service_discovery_private_dns_namespace" "main" {
  name        = "${var.project_name}-${var.environment}.local"
  vpc         = var.vpc_id

  tags = {
    Name        = "${var.project_name}-${var.environment}.local"
    Environment = var.environment
    Project     = var.project_name
  }
}

resource "aws_service_discovery_service" "flask" {
  name = "flask"

  dns_config {
    namespace_id = aws_service_discovery_private_dns_namespace.main.id

    dns_records {
      ttl  = 10
      type = "A"
    }
  }

  health_check_custom_config {
    failure_threshold = 1
  }
}
resource "aws_cloudwatch_log_group" "observability" {
  name              = "/ecs/${var.project_name}-${var.environment}-observability"
  retention_in_days = 14

  tags = {
    Name        = "${var.project_name}-${var.environment}-observability-logs"
    Environment = var.environment
    Project     = var.project_name
  }
}
resource "aws_ecs_task_definition" "observability" {
  family                   = "${var.project_name}-${var.environment}-observability"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "512"
  memory                   = "1024"
  execution_role_arn       = aws_iam_role.observability_execution_role.arn
  task_role_arn            = aws_iam_role.observability_task_role.arn

  container_definitions = jsonencode([
    {
      name      = "prometheus"
      image     = "${aws_ecr_repository.prometheus.repository_url}:latest"
      essential = true
      portMappings = [{
        containerPort = 9090
        protocol      = "tcp"
      }]
      command = [
        "--config.file=/etc/prometheus/prometheus.yml"
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = "/ecs/${var.project_name}-${var.environment}-observability"
          awslogs-region        = "us-east-1"
          awslogs-stream-prefix = "prometheus"
        }
      }
    },
    {
      name      = "grafana"
      image     = "grafana/grafana:latest"
      essential = true
      portMappings = [{
        containerPort = 3000
        protocol      = "tcp"
      }]
      environment = [
        {
          name  = "GF_SECURITY_ADMIN_PASSWORD"
          value = "secretive-admin-2026"
        },
        {
          name  = "GF_SERVER_HTTP_PORT"
          value = "3000"
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = "/ecs/${var.project_name}-${var.environment}-observability"
          awslogs-region        = "us-east-1"
          awslogs-stream-prefix = "grafana"
        }
      }
    }
  ])

  tags = {
    Name        = "${var.project_name}-${var.environment}-observability-task"
    Environment = var.environment
    Project     = var.project_name
  }
}
resource "aws_ecs_service" "observability" {
  name            = "${var.project_name}-${var.environment}-observability-service"
  cluster         = var.ecs_cluster_id
  task_definition = aws_ecs_task_definition.observability.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.public_subnet_ids
    security_groups  = [var.grafana_sg_id, var.prometheus_sg_id]
    assign_public_ip = true
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-observability-service"
    Environment = var.environment
    Project     = var.project_name
  }
}
resource "aws_ecr_repository" "prometheus" {
  name = "${var.project_name}-${var.environment}-prometheus"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-prometheus"
    Environment = var.environment
    Project     = var.project_name
  }
}