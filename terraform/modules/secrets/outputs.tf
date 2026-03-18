output "meta_api_token_arn" {
  description = "ARN of the Meta API token secret"
  value       = aws_secretsmanager_secret.meta_api_token.arn
}

output "google_sheets_credentials_arn" {
  description = "ARN of the Google Sheets credentials secret"
  value       = aws_secretsmanager_secret.google_sheets_credentials.arn
}