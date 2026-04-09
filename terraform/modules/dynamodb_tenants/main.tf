terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "5.81.0"
    }
  }
}

resource "aws_dynamodb_table" "tenant_tokens" {
  name         = "${var.project_name}-${var.environment}-tenant-tokens"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "instagram_account_id"

  attribute {
    name = "instagram_account_id"
    type = "S"
  }

  ttl {
    attribute_name = "token_expiry"
    enabled        = true
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-tenant-tokens"
    Environment = var.environment
    Project     = var.project_name
  }
}