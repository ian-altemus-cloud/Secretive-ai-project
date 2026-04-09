terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "5.81.0"
    }
  }
}

resource "aws_kms_key" "tenant_tokens" {
  description             = "SilverLink tenant OAuth token encryption"
  deletion_window_in_days = 30
  enable_key_rotation     = true

  tags = {
    Name        = "${var.project_name}-${var.environment}-tenant-tokens-key"
    Environment = var.environment
    Project     = var.project_name
  }
}

resource "aws_kms_alias" "tenant_tokens" {
  name          = "alias/${var.project_name}-${var.environment}-tenant-tokens"
  target_key_id = aws_kms_key.tenant_tokens.key_id
}