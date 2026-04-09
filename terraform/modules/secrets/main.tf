terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "5.81.0"
    }
  }
}
resource "aws_secretsmanager_secret" "meta_api_token" {
  name        = "${var.project_name}-${var.environment}/meta-api-token"
  description = "Meta Graph API access token for Instagram DM webhook"

  tags = {
    Name        = "${var.project_name}-${var.environment}-meta-api-token"
    Environment = var.environment
    Project     = var.project_name
  }
}

resource "aws_secretsmanager_secret" "google_sheets_credentials" {
  name        = "${var.project_name}/${var.environment}/google-sheets-credentials"
  description = "Google Sheets service account JSON credentials"

  tags = {
    Name        = "${var.project_name}-${var.environment}-google-sheets-credentials"
    Environment = var.environment
    Project     = var.project_name
  }
}
resource "aws_secretsmanager_secret" "jwt_secret_key" {
  name                    = "${var.project_name}-${var.environment}/jwt-secret-key"
  description             = "JWT signing key for OAuth state parameter validation"
  recovery_window_in_days = 30

tags = {
    Name                  = "${var.project_name}-${var.environment}-jwt-secret-key"
    Environment           = var.environment
    Project               = var.project_name
  }
}
