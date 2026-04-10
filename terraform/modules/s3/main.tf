resource "aws_s3_bucket" "prompt_store" {
  bucket = "${var.project_name}-${var.environment}-prompt-store"

  tags = {
    Project     = var.project_name
    Environment = var.environment
    Purpose     = "client-prompt-store"
  }
}

resource "aws_s3_bucket_versioning" "prompt_store" {
  bucket = aws_s3_bucket.prompt_store.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "prompt_store" {
  bucket = aws_s3_bucket.prompt_store.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "aws:kms"
      kms_master_key_id = var.kms_key_arn
    }
  }
}

resource "aws_s3_bucket_public_access_block" "prompt_store" {
  bucket = aws_s3_bucket.prompt_store.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}