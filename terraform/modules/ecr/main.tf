resource "aws_ecr_repository" "ecr_repository" {
  name                 = "${var.project_name}-${var.environment}-ecr"
  image_tag_mutability = var.image_tag_mutability
  image_scanning_configuration {
    scan_on_push = var.scan_on_push
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-ecr"
    Environment = var.environment
    Project     = var.project_name
  }
}