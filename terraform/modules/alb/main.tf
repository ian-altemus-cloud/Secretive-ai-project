terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "5.81.0"
    }
  }
}

resource "aws_lb" "main" {
  name               = "${var.project_name}-${var.environment}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups = [var.alb_sg_id]
  subnets = var.public_subnet_ids

  tags = {
    Name = "${var.project_name}-${var.environment}-alb"
    Environment = var.environment
    Project     = var.project_name
  }
}

resource "aws_lb_target_group" "flask" {
  name = "${var.project_name}-${var.environment}-tg"
  port = 80
  protocol = "HTTP"
  vpc_id = var.vpc_id
  target_type = "ip"

  health_check {
    path = "/webhook"
    protocol = "HTTP"
    matcher = "200,403"
    interval = 30
    timeout = 5
    healthy_threshold = 2
    unhealthy_threshold = 3
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-tg"
    Environment = var.environment
    Project = var.project_name
  }
}


resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port = 80
  protocol = "HTTP"

  default_action {
    type = "fixed-response"
    fixed_response {
      content_type = "application/json"
      message_body = "{\"error\": \"Not found\"}"
      status_code = "404"
    }
  }
}

resource "aws_lb_listener_rule" "conversations" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 10

  condition {
    path_pattern {
      values = ["/api/conversations"]
    }
  }

  action {
    type = "forward"
    target_group_arn = aws_lb_target_group.flask.arn
  }
}

resource "aws_lb_listener_rule" "webhook_get" {
  listener_arn = "aws_lb_listener.http.arn"
  priority = 20

  condition {
    path_pattern {
      values = ["/webhook"]
    }
  }

  condition {
    http_request_method {
      values = ["GET"]
    }
  }
  action {
    type = "forward"
    target_group_arn = aws_lb_target_group.flask.arn
  }
}

resource "aws_lb_listener_rule" "webhook_post" {
  listener_arn = aws_lb_listener.http.arn
  priority = 30

  condition {
    path_pattern {
      values = ["/webhook"]
    }
  }
  condition {
    http_request_method {
      values = ["POST"]
    }
  }

  action {
    type = "forward"
    target_group_arn = aws_lb_target_group.flask.arn
  }
}