output "dynamodb_table_arn" {
  description = "Arn of the DynamoDB table"
  value = aws_dynamodb_table.dynamodb_table.arn
}

output "dynamodb_table_name" {
  description = "Name of the DynamoDB table"
  value = aws_dynamodb_table.dynamodb_table.name
}

