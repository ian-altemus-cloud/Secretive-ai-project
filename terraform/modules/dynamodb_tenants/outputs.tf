output "tenant_table_arn" {
  value = aws_dynamodb_table.tenant_tokens.arn
}

output "tenant_table_name" {
  value = aws_dynamodb_table.tenant_tokens.name
}