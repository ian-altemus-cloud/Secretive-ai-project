output "api_gateway_url" {
  description = "Public URL of the API Gateway webhook endpoint"
  value       = "${aws_api_gateway_stage.main.invoke_url}/webhook"
}

output "api_gateway_id" {
  description = "ID of the API Gateway REST API"
  value       = aws_api_gateway_rest_api.main.id
}