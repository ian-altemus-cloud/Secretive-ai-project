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