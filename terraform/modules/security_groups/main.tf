resource "aws_security_group" "alb" {
  name        = "${var.project_name}-${var.environment}-alb-sg"
  description = "Security group for Application load balancer"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTPS from internet"
  }

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTP redirect to HTTPS"
  }

  egress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
    description = "HTTP to Fargate"
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-alb-sg"
    Environment = var.environment
    Project     = var.project_name
  }
}

resource "aws_security_group" "fargate" {
  name        = "${var.project_name}-${var.environment}-fargate-sg"
  description = "Security group for Fargate tasks"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = 80
    to_port         = 80
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
    description     = "HTTP from ALB only"
  }
   ingress {
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.prometheus.id]
    description     = "Allow Prometheus to scrape metrics"
  }
  egress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTPS to Bedrock, DynamoDB, SQS, Meta, Google"
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-fargate-sg"
    Environment = var.environment
    Project     = var.project_name
  }
}
resource "aws_security_group" "grafana" {
  name        = "${var.project_name}-${var.environment}-grafana-sg"
  description = "Security group for grafana tasks"
  vpc_id      = var.vpc_id

  egress {
    from_port   = 9090
    to_port     = 9090
    protocol    = "tcp"
    security_groups = [aws_security_group.prometheus.id]
    description = "Allow only outbound to prometheus sg"
  }
  ingress {
    from_port   = 3000
    to_port     = 3000
    protocol    = "tcp"
    cidr_blocks = ["76.32.56.93/32"]
    description = "Allow only inbound from the internet"
  }

    tags = {
    Name        = "${var.project_name}-${var.environment}-grafana-sg"
    Environment = var.environment
    Project     = var.project_name
  }
}

resource "aws_security_group" "prometheus" {
  name        = "${var.project_name}-${var.environment}-prometheus-sg"
  description = "Security group for prometheus tasks"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 9090
    to_port     = 9090
    protocol    = "tcp"
    security_groups = [aws_security_group.grafana.id]
    description = "Allow only inbound from grafana sg"
  }
  egress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    security_groups = [aws_security_group.fargate.id]
    description = "Allow only outbound to fargate flask app"
  }
    tags = {
    Name        = "${var.project_name}-${var.environment}-prometheus-sg"
    Environment = var.environment
    Project     = var.project_name
  }
}