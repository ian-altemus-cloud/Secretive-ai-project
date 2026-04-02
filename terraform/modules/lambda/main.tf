terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "5.81.0"
    }
  }
}

resource "aws_lambda_function" "followup" {
  function_name = "${var.project_name}-${var.environment}-followup"
  role          = aws_iam_role.lambda_execution_role.arn
  runtime       = "python3.11"
  handler       = "followup_lambda.lambda_handler"
  filename      = "${path.module}/../../../app/src/followup_lambda.zip"

  memory_size = var.memory
  timeout     = 30

  vpc_config {
    subnet_ids         = var.private_subnet_ids
    security_group_ids = [var.lambda_sg_id]
  }

  environment {
    variables = {
      DYNAMODB_TABLE_NAME    = var.dynamodb_table_name
      META_API_TOKEN_ARN     = var.meta_api_token_arn
      ANTHROPIC_API_KEY_ARN  = var.anthropic_api_secret_arn
      GOOGLE_SHEETS_SECRET_ARN = var.google_sheets_secret_arn
    }
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-followup"
    Environment = var.environment
    Project     = var.project_name
  }
}

resource "aws_iam_role" "lambda_execution_role" {
  name = "${var.project_name}-${var.environment}-followup-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })

  tags = {
    Name        = "${var.project_name}-${var.environment}-followup-lambda-role"
    Environment = var.environment
    Project     = var.project_name
  }
}
resource "aws_iam_role_policy" "lambda_policy" {
  name = "${var.project_name}-${var.environment}-followup-lambda-policy"
  role = aws_iam_role.lambda_execution_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem"
        ]
        Resource = var.dynamodb_table_arn
      },
      {
        Effect = "Allow"
        Action = ["secretsmanager:GetSecretValue"]
        Resource = [
          var.meta_api_token_arn,
          var.anthropic_api_secret_arn,
          var.google_sheets_secret_arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "ec2:CreateNetworkInterface",
          "ec2:DescribeNetworkInterfaces",
          "ec2:DeleteNetworkInterface"
        ]
        Resource = "*"
      }
    ]
  })
}
resource "aws_cloudwatch_log_group" "main" {
  name              = "/lambda/${var.project_name}-${var.environment}-followup"
  retention_in_days = 14

  tags = {
    Name        = "${var.project_name}-${var.environment}-followup-logs"
    Environment = var.environment
    Project     = var.project_name
  }
}
resource "aws_iam_role" "scheduler_role" {
  name = "${var.project_name}-${var.environment}-scheduler-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "scheduler.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}
resource "aws_iam_role_policy" "scheduler_policy" {
  name = "${var.project_name}-${var.environment}-scheduler-policy"
  role = aws_iam_role.scheduler_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["lambda:InvokeFunction"]
      Resource = aws_lambda_function.followup.arn
    }]
  })
}