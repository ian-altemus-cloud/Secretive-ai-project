terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "5.81.0"
    }
  }
}

resource "aws_ecs_cluster" "main" {
  name = "${var.project_name}-${var.environment}-cluster"

  tags = {
    Name = "${var.project_name}-${var.environment}-cluster"
  }
}

resource "aws_iam_role" "ecs_execution_role" {
  name = "${var.project_name}-${var.environment}-ecs-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })

  tags = {
    Name        = "${var.project_name}-${var.environment}-ecs-execution-role"
    Environment = var.environment
    Project     = var.project_name
  }
}

resource "aws_iam_role_policy_attachment" "ecs_execution_role_policy" {
  role       = aws_iam_role.ecs_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role" "ecs_task_role" {
  name = "${var.project_name}-${var.environment}-ecs-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })

  tags = {
    Name        = "${var.project_name}-${var.environment}-ecs-task-role"
    Environment = var.environment
    Project     = var.project_name
  }
}
resource "aws_ecs_task_definition" "main" {
  family                   = "${var.project_name}-${var.environment}"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.cpu
  memory                   = var.memory
  execution_role_arn       = aws_iam_role.ecs_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([{
    name      = "${var.project_name}-${var.environment}"
    image     = var.container_image
    essential = true
    portMappings = [{
      containerPort = var.container_port
      protocol      = "tcp"
    }]

    environment = [
      {
        name  = "DYNAMODB_TABLE_NAME"
        value = "${var.project_name}-${var.environment}-dynamodb"
      },
      {
        name  = "SQS_QUEUE_URL"
        value = "https://sqs.us-east-1.amazonaws.com/894943009636/${var.project_name}-${var.environment}-queue"
      },
      {
        name  = "AWS_DEFAULT_REGION"
        value = "us-east-1"
      },
      {
        name  = "BEDROCK_MODEL_ID"
        value = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
      },
      {
        name  = "PYTHONUNBUFFERED"
        value = "1"
      },
      {
        name  = "AI_PROVIDER"
        value = "anthropic"
      },
      {
        name  = "GOOGLE_SPREADSHEET_ID"
        value = "1hcom7y5xzJP2V0GhHDeCUtE7Ms0r7KNX8xoTvjpfZIY"
      },
      {
        name  = "GOOGLE_SHEETS_SECRET_ARN"
        value = "arn:aws:secretsmanager:us-east-1:894943009636:secret:secretive-nail-bar/dev/google-sheets-credentials-IM5gxg"
      },
      {
        name  = "FOLLOWUP_LAMBDA_ARN"
        value = var.followup_lambda_arn
      },
      {
        name  = "SCHEDULER_ROLE_ARN"
        value = var.scheduler_role_arn
      },
      {
        name  = "DASHBOARD_API_KEY_ARN"
        value = "arn:aws:secretsmanager:us-east-1:894943009636:secret:sl_dashboard_api_key-5h8EKS"
      },
    ]

    secrets = [
      {
        name      = "ANTHROPIC_API_KEY"
        valueFrom = "arn:aws:secretsmanager:us-east-1:894943009636:secret:secretive-api-key-JLF2jL"
      },
      {
        name      = "META_APP_SECRET"
        valueFrom = "arn:aws:secretsmanager:us-east-1:894943009636:secret:META_APP_SECRET-JTVhID"
      },
      {
        name      = "META_ACCESS_TOKEN"
        valueFrom = "arn:aws:secretsmanager:us-east-1:894943009636:secret:META-ACCESS-TOKEN-Yf2TBG"
      },
      {
        name      = "META_VERIFY_TOKEN"
        valueFrom = "arn:aws:secretsmanager:us-east-1:894943009636:secret:meta-verify-token-SHC3HQ"
      }
    ]

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        awslogs-group         = "/ecs/${var.project_name}-${var.environment}"
        awslogs-region        = "us-east-1"
        awslogs-stream-prefix = "ecs"
      }
    }
  }])

  tags = {
    Name        = "${var.project_name}-${var.environment}-task"
    Environment = var.environment
    Project     = var.project_name
  }
}

resource "aws_ecs_service" "main" {
  name            = "${var.project_name}-${var.environment}-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.main.arn
  desired_count   = var.desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [var.fargate_sg_id]
    assign_public_ip = false
  }
  load_balancer {
    target_group_arn = var.target_group_arn
    container_name   = "${var.project_name}-${var.environment}"
    container_port   = 80
  }

  service_registries {
    registry_arn = "arn:aws:servicediscovery:us-east-1:894943009636:service/srv-rcr3ar5s6rhreibx"
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-service"
    Environment = var.environment
    Project     = var.project_name
  }
}

resource "aws_cloudwatch_log_group" "main" {
  name              = "/ecs/${var.project_name}-${var.environment}"
  retention_in_days = 14
}

resource "aws_iam_role_policy" "ecs_task_policy" {
  name = "${var.project_name}-${var.environment}-ecs-task-policy"
  role = aws_iam_role.ecs_task_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["sqs:ReceiveMessage", "sqs:DeleteMessage", "sqs:SendMessage"]
        Resource = var.sqs_queue_arn
      },
      {
        Effect   = "Allow"
        Action   = ["dynamodb:GetItem", "dynamodb:PutItem", "dynamodb:UpdateItem", "dynamodb:Query"]
        Resource = var.dynamodb_table_arn
      },
      {
        Effect = "Allow"
        Action = [
          "scheduler:CreateSchedule",
          "scheduler:DeleteSchedule",
          "scheduler:GetSchedule",
          "scheduler:UpdateSchedule"
        ]
        Resource = "arn:aws:scheduler:us-east-1:894943009636:schedule/default/follow-up-*"
      },
      {
        Effect   = "Allow"
        Action   = ["iam:PassRole"]
        Resource = "arn:aws:iam::894943009636:role/${var.project_name}-${var.environment}-scheduler-role"
      },
      {
        Effect = "Allow"
        Action = ["bedrock:InvokeModel"]
        Resource = [
          "arn:aws:bedrock:*::foundation-model/anthropic.claude-haiku-4-5-20251001-v1:0",
          "arn:aws:bedrock:us-east-1:894943009636:inference-profile/us.anthropic.claude-haiku-4-5-20251001-v1:0"
        ]
      },
      {
        Effect = "Allow"
        Action = ["secretsmanager:GetSecretValue"]
        Resource = [var.google_sheets_secret_arn,
          "arn:aws:secretsmanager:us-east-1:894943009636:secret:sl_dashboard_api_key-5h8EKS"
        ]
      }
    ]
  })
}
resource "aws_iam_role_policy" "ecs_execution_secrets_policy" {
  name = "${var.project_name}-${var.environment}-ecs-execution-secrets-policy"
  role = aws_iam_role.ecs_execution_role.id


  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = ["secretsmanager:GetSecretValue"]
        Resource = [
          "arn:aws:secretsmanager:us-east-1:894943009636:secret:secretive-api-key-JLF2jL",
          "arn:aws:secretsmanager:us-east-1:894943009636:secret:secretive-nail-bar/dev/google-sheets-credentials-IM5gxg",
          "arn:aws:secretsmanager:us-east-1:894943009636:secret:META_APP_SECRET-JTVhID",
          "arn:aws:secretsmanager:us-east-1:894943009636:secret:META-ACCESS-TOKEN-Yf2TBG",
          "arn:aws:secretsmanager:us-east-1:894943009636:secret:meta-verify-token-SHC3HQ"
        ]
      }
    ]
  })
}