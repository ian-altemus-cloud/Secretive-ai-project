output "vpc_id" {
  description = "ID of the VPC"
  value       = "aws_vpc.main.id"
}

output "public_subnet_ids" {
  description = "IDs of the public subnets"
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "IDs of the private subnets"
  value       = aws_subnet.private[*].id
}

output "nat_gateway_id" {
  description = "ID of the Nat Gateway"
  value       = aws_nat_gateway.main.id
}

output "internet_gateway_id" {
  description = "ID of the Internet Gateway"
  value       = aws_internet_gateway.main.id
}

output "vpc_endpoint_dynamodb_id" {
  description = "ID of the DynamoDB VPC endpoint"
  value = aws_vpc_endpoint.dynamodb.id
}

output "vpc_endpoint_bedrock_id" {
  description = "ID of the Bedrock VPC endpoint"
  value = aws_vpc_endpoint.bedrock.id
}

output "vpc_endpoints_sg_id" {
  description = "ID of the VPC endpoints security group"
  value       = aws_security_group.vpc_endpoints.id
}