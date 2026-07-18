locals {
  scheme        = var.internal ? "internal" : "internet-facing"
  enable_https  = var.certificate_arn != ""
}

# ── Security Group ───────────────────────────────────────────────────────

resource "aws_security_group" "this" {
  name_prefix = "${var.name_prefix}-alb-"
  description = "Security group for ALB"
  vpc_id      = var.vpc_id

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  dynamic "ingress" {
    for_each = local.enable_https ? [1] : []
    content {
      description = "HTTPS"
      from_port   = 443
      to_port     = 443
      protocol    = "tcp"
      cidr_blocks = ["0.0.0.0/0"]
    }
  }

  egress {
    description = "All traffic to VPC"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-alb-sg"
  })
}

# ── Application Load Balancer ────────────────────────────────────────────

resource "aws_lb" "this" {
  name               = "${var.name_prefix}-alb"
  internal           = var.internal
  load_balancer_type = "application"
  security_groups    = concat(var.security_group_ids, [aws_security_group.this.id])
  subnets            = var.subnet_ids

  enable_http2                     = var.enable_http2
  idle_timeout                     = var.idle_timeout
  enable_deletion_protection       = var.deletion_protection
  drop_invalid_header_fields       = var.drop_invalid_header_fields
  preserve_host_header             = var.preserve_host_header

  dynamic "access_logs" {
    for_each = var.access_logs_bucket != "" ? [1] : []
    content {
      bucket  = var.access_logs_bucket
      prefix  = var.access_logs_prefix
      enabled = true
    }
  }

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-alb"
  })
}

# ── Target Group ─────────────────────────────────────────────────────────

resource "aws_lb_target_group" "main" {
  name_prefix = "${substr(var.name_prefix, 0, 6)}-tg"
  port        = var.target_group_port
  protocol    = var.target_group_protocol
  vpc_id      = var.vpc_id
  target_type = "ip"

  deregistration_delay = var.deregistration_delay

  health_check {
    enabled             = true
    healthy_threshold   = 3
    unhealthy_threshold = 3
    timeout             = 10
    interval            = 30
    path                = var.health_check_path
    port                = var.health_check_port
    matcher             = var.health_check_matcher
    protocol            = "HTTP"
  }

  stickiness {
    type            = "lb_cookie"
    cookie_duration = 86400
    enabled         = true
  }

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-tg"
  })

  lifecycle {
    create_before_destroy = true
  }
}

# ── HTTP Listener (redirect to HTTPS) ────────────────────────────────────

resource "aws_lb_listener" "http" {
  count             = local.enable_https ? 1 : 0
  load_balancer_arn = aws_lb.this.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type = "redirect"

    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
      query       = "#{query}"
      host        = "#{host}"
      path        = "/#{path}"
    }
  }
}

resource "aws_lb_listener" "http_forward" {
  count             = local.enable_https ? 0 : 1
  load_balancer_arn = aws_lb.this.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.main.arn
  }
}

# ── HTTPS Listener ───────────────────────────────────────────────────────

resource "aws_lb_listener" "https" {
  count             = local.enable_https ? 1 : 0
  load_balancer_arn = aws_lb.this.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = var.ssl_policy
  certificate_arn   = var.certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.main.arn
  }
}

# ── Additional Target Groups and Rules ───────────────────────────────────

resource "aws_lb_target_group" "additional" {
  for_each = var.additional_target_groups

  name_prefix = "${substr(var.name_prefix, 0, 4)}-${each.key}"
  port        = each.value.port
  protocol    = each.value.protocol
  vpc_id      = var.vpc_id
  target_type = "ip"

  deregistration_delay = var.deregistration_delay

  health_check {
    enabled             = true
    healthy_threshold   = 3
    unhealthy_threshold = 3
    timeout             = 10
    interval            = 30
    path                = each.value.health_check_path
    port                = "traffic-port"
    matcher             = each.value.health_check_matcher
  }

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-${each.key}-tg"
  })

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_lb_listener_rule" "additional" {
  for_each = var.additional_target_groups

  listener_arn = local.enable_https ? aws_lb_listener.https[0].arn : aws_lb_listener.http_forward[0].arn
  priority     = each.value.priority

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.additional[each.key].arn
  }

  condition {
    host_header {
      values = [each.value.host_header]
    }
  }

  condition {
    path_pattern {
      values = [each.value.path_pattern]
    }
  }
}

# ── WAF Association ──────────────────────────────────────────────────────

resource "aws_wafv2_web_acl_association" "this" {
  count        = var.waf_arn != "" ? 1 : 0
  resource_arn = aws_lb.this.arn
  web_acl_arn  = var.waf_arn
}
