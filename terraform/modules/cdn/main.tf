locals {
  has_alb_origin    = var.alb_origin_domain != ""
  has_s3_origin     = var.s3_origin_bucket_name != ""
  has_waf           = var.waf_arn != ""
  has_custom_domain = length(var.aliases) > 0 && var.acm_certificate_arn != ""
  has_logs          = var.log_bucket_name != ""
}

# ── Origin Access Control for S3 ─────────────────────────────────────────

resource "aws_cloudfront_origin_access_control" "s3" {
  count                              = local.has_s3_origin ? 1 : 0
  name                               = "${var.name_prefix}-s3-oac"
  description                        = "OAC for S3 static assets origin"
  origin_access_control_origin_type  = "s3"
  signing_behavior                   = "always"
  signing_protocol                   = "sigv4"
}

# ── CloudFront Distribution ──────────────────────────────────────────────

resource "aws_cloudfront_distribution" "this" {
  enabled             = true
  is_ipv6_enabled     = true
  comment             = "CloudFront distribution for ${var.name_prefix}"
  default_root_object = var.default_root_object
  price_class         = var.price_class
  aliases             = var.aliases
  http_version        = "http2and3"

  dynamic "origin" {
    for_each = local.has_alb_origin ? [1] : []
    content {
      domain_name = var.alb_origin_domain
      origin_id   = "${var.name_prefix}-alb-origin"
      origin_path = ""

      custom_origin_config {
        http_port              = var.alb_origin_http_port
        https_port             = var.alb_origin_https_port
        origin_protocol_policy = "https-only"
        origin_ssl_protocols   = ["TLSv1.2"]
        origin_keepalive_timeout = 60
        origin_read_timeout      = 60
      }

    }
  }

  dynamic "origin" {
    for_each = local.has_s3_origin ? [1] : []
    content {
      domain_name              = var.s3_origin_bucket_name != "" ? data.aws_s3_bucket.static[0].bucket_regional_domain_name : ""
      origin_id                = "${var.name_prefix}-s3-origin"
      origin_access_control_id = aws_cloudfront_origin_access_control.s3[0].id
    }
  }

  dynamic "logging_config" {
    for_each = local.has_logs ? [1] : []
    content {
      include_cookies = false
      bucket          = "${var.log_bucket_name}.s3.amazonaws.com"
      prefix          = var.log_prefix
    }
  }

  default_cache_behavior {
    target_origin_id       = local.has_alb_origin ? "${var.name_prefix}-alb-origin" : "${var.name_prefix}-s3-origin"
    viewer_protocol_policy = "redirect-to-https"
    compress               = true
    allowed_methods        = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods         = ["GET", "HEAD"]
    smooth_streaming       = false

    forwarded_values {
      query_string = var.forward_query_string
      headers      = ["Origin", "Authorization", "Accept", "Referer", "CloudFront-Forwarded-Proto"]

      cookies {
        forward = var.forward_cookies
      }
    }

    min_ttl     = 0
    default_ttl = 0
    max_ttl     = 31536000

    dynamic "lambda_function_association" {
      for_each = var.lambda_edge_security_headers_arn != "" ? [1] : []
      content {
        event_type   = "origin-response"
        lambda_arn   = var.lambda_edge_security_headers_arn
        include_body = false
      }
    }

    function_association {
      event_type   = "viewer-request"
      function_arn = aws_cloudfront_function.redirect_handler.arn
    }
  }

  ordered_cache_behavior {
    path_pattern           = "/static/*"
    target_origin_id       = local.has_s3_origin ? "${var.name_prefix}-s3-origin" : "${var.name_prefix}-alb-origin"
    viewer_protocol_policy = "redirect-to-https"
    compress               = true
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods         = ["GET", "HEAD"]

    forwarded_values {
      query_string = false
      headers      = ["Origin"]

      cookies {
        forward = "none"
      }
    }

    min_ttl     = 0
    default_ttl = 86400
    max_ttl     = 31536000
  }

  ordered_cache_behavior {
    path_pattern           = "/assets/*"
    target_origin_id       = local.has_s3_origin ? "${var.name_prefix}-s3-origin" : "${var.name_prefix}-alb-origin"
    viewer_protocol_policy = "redirect-to-https"
    compress               = true
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods         = ["GET", "HEAD"]

    forwarded_values {
      query_string = false
      headers      = ["Origin"]

      cookies {
        forward = "none"
      }
    }

    min_ttl     = 0
    default_ttl = 86400
    max_ttl     = 31536000
  }

  ordered_cache_behavior {
    path_pattern           = "/api/*"
    target_origin_id       = "${var.name_prefix}-alb-origin"
    viewer_protocol_policy = "https-only"
    compress               = true
    allowed_methods        = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods         = ["GET", "HEAD"]

    forwarded_values {
      query_string = true
      headers      = ["Authorization", "Origin", "Accept", "CloudFront-Forwarded-Proto"]

      cookies {
        forward = "all"
      }
    }

    min_ttl     = 0
    default_ttl = 0
    max_ttl     = 0
  }

  dynamic "custom_error_response" {
    for_each = var.custom_error_responses
    content {
      error_code            = custom_error_response.value.error_code
      response_page_path    = custom_error_response.value.response_page_path
      response_code         = custom_error_response.value.response_code
      error_caching_min_ttl = custom_error_response.value.ttl
    }
  }

  dynamic "geo_restriction" {
    for_each = var.geo_restriction_type != "none" ? [1] : []
    content {
      restriction_type = var.geo_restriction_type
      locations        = var.geo_restriction_locations
    }
  }

  web_acl_id = local.has_waf ? var.waf_arn : null

  viewer_certificate {
    cloudfront_default_certificate = !local.has_custom_domain
    acm_certificate_arn            = local.has_custom_domain ? var.acm_certificate_arn : null
    ssl_support_method             = local.has_custom_domain ? "sni-only" : null
    minimum_protocol_version       = var.minimum_protocol_version
  }

  retain_on_delete = false

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-cdn"
  })
}

# ── CloudFront Function (redirect handler) ───────────────────────────────

resource "aws_cloudfront_function" "redirect_handler" {
  name    = "${var.name_prefix}-redirect-handler"
  runtime = "cloudfront-js-2.0"
  comment = "Adds trailing slash and handles index.html fallback"
  code    = file("${path.module}/redirect_handler.js")
}

# ── Data Sources ─────────────────────────────────────────────────────────

data "aws_s3_bucket" "static" {
  count  = local.has_s3_origin ? 1 : 0
  bucket = var.s3_origin_bucket_name
}
