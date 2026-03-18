output "sqs_url" {
  description = "The url of the sqs queue"
  value       = aws_sqs_queue.main.url
}

output "sqs_arn" {
  description = "The ARN of the SQS for internal ntwk"
  value       = aws_sqs_queue.main.arn
}

output "dlq_url" {
  description = "the url of the DLQ"
  value       = aws_sqs_queue.dlq.url
}

output "dlq_arn" {
  description = "The ARN of the DLQ"
  value       = aws_sqs_queue.dlq.arn
}