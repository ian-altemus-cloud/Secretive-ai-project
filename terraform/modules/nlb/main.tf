terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "5.81.0"
    }
  }
}

resource "aws_lb" "nlb" {
  name               = "${var.project_name}-${var.environment}-nlb"
  internal           = true
  load_balancer_type = "network"
  subnets            = var.private_subnet_ids

  tags = {
    Name        = "${var.project_name}-${var.environment}-nlb"
    Environment = var.environment
    Project     = var.project_name
  }
}

resource "aws_lb_target_group" "flask" {
  name        = "${var.project_name}-${var.environment}-nlb-tg"
  port        = 80
  protocol    = "TCP"
  vpc_id      = var.vpc_id
  target_type = "ip"

  health_check {
    protocol            = "HTTP"
    path                = "/webhook"
    matcher             = "200,403"
    interval            = 30
    healthy_threshold   = 2
    unhealthy_threshold = 3
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-nlb-tg"
    Environment = var.environment
    Project     = var.project_name
  }
}

resource "aws_lb_listener" "nlb" {
  load_balancer_arn = aws_lb.nlb.arn
  port              = 80
  protocol          = "TCP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.flask.arn
  }
}