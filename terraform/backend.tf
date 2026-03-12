terraform {
  backend "s3" {
    bucket         = "secretive-ai-terraform-state"
    key            = "secretive-nail-bar/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "secretive-ai-terraform-locks"
    encrypt        = true
  }
}