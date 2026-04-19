resource "aws_sqs_queue" "dlq" {
  name                      = "${var.project_name}-${var.environment}-dlq"
  message_retention_seconds = var.message_retention_seconds

  tags = {
    Name        = "${var.project_name}-${var.environment}-dlq"
    Environment = var.environment
    Project     = var.project_name
  }
}

resource "aws_sqs_queue" "main" {
  name                       = "${var.project_name}-${var.environment}-queue"
  visibility_timeout_seconds = var.visibility_timeout_seconds
  message_retention_seconds  = var.message_retention_seconds

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount     = var.max_receive_count
  })

  tags = {
    Name        = "${var.project_name}-${var.environment}-queue"
    Environment = var.environment
    Project     = var.project_name
  }
}

resource "aws_sqs_queue" "agent_dlq" {
  name                      = "${var.project_name}-${var.environment}-agent-dlq"
  message_retention_seconds = var.message_retention_seconds
  tags = {
    Name        = "${var.project_name}-${var.environment}-agent-dlq"
    Environment = var.environment
    Project     = var.project_name
  }
}

resource "aws_sqs_queue" "agent_queue" {
  name                       = "${var.project_name}-${var.environment}-agent-queue"
  visibility_timeout_seconds = var.visibility_timeout_seconds
  message_retention_seconds  = var.message_retention_seconds
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.agent_dlq.arn
    maxReceiveCount     = var.max_receive_count
  })
  tags = {
    Name        = "${var.project_name}-${var.environment}-agent-queue"
    Environment = var.environment
    Project     = var.project_name
  }
}

resource "aws_sqs_queue" "agent_results_dlq" {
  name                      = "${var.project_name}-${var.environment}-agent-results-dlq"
  message_retention_seconds = var.message_retention_seconds
  tags = {
    Name        = "${var.project_name}-${var.environment}-agent-results-dlq"
    Environment = var.environment
    Project     = var.project_name
  }
}

resource "aws_sqs_queue" "agent_results_queue" {
  name                       = "${var.project_name}-${var.environment}-agent-results-queue"
  visibility_timeout_seconds = var.visibility_timeout_seconds
  message_retention_seconds  = var.message_retention_seconds
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.agent_results_dlq.arn
    maxReceiveCount     = var.max_receive_count
  })
  tags = {
    Name        = "${var.project_name}-${var.environment}-agent-results-queue"
    Environment = var.environment
    Project     = var.project_name
  }
}