output "bucket_name" {
  description = "Name of the prompt store S3 bucket"
  value       = aws_s3_bucket.prompt_store.bucket
}

output "bucket_arn" {
  description = "ARN of the prompt store S3 bucket"
  value       = aws_s3_bucket.prompt_store.arn
}