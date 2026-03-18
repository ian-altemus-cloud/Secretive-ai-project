resource "aws_dynamodb_table" "dynamodb_table" {
  name         = "${var.project_name}-${var.environment}-dynamodb"
  billing_mode = var.billing_mode
  hash_key     = var.hash_key

  attribute {
    name = "instagram_user_id"
    type = "S"
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-dynamodb"
    Environment = var.environment
    Project     = var.project_name
  }
}