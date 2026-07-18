locals {
  has_alb = var.alb_dns_name != ""
  has_cdn = var.cdn_domain_name != ""
  has_private = var.create_private_zone && var.vpc_id != ""
  has_failover = var.enable_failover && var.primary_alb_dns_name != "" && var.secondary_alb_dns_name != ""
  has_latency = var.enable_latency_routing && length(var.latency_records) > 0
}

# ── Public Zone ──────────────────────────────────────────────────────────

resource "aws_route53_zone" "public" {
  count = var.create_public_zone ? 1 : 0
  name  = var.domain_name

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-public-zone"
  })
}

# ── Private Zone ─────────────────────────────────────────────────────────

resource "aws_route53_zone" "private" {
  count = local.has_private ? 1 : 0
  name  = "internal.${var.domain_name}"

  vpc {
    vpc_id = var.vpc_id
  }

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-private-zone"
  })
}

# ── ALB A Record (alias) ─────────────────────────────────────────────────

resource "aws_route53_record" "alb" {
  count   = local.has_alb ? 1 : 0
  zone_id = aws_route53_zone.public[0].zone_id
  name    = var.domain_name
  type    = "A"

  alias {
    name                   = var.alb_dns_name
    zone_id                = var.alb_zone_id
    evaluate_target_health = true
  }
}

resource "aws_route53_record" "alb_aaaa" {
  count   = local.has_alb ? 1 : 0
  zone_id = aws_route53_zone.public[0].zone_id
  name    = var.domain_name
  type    = "AAAA"

  alias {
    name                   = var.alb_dns_name
    zone_id                = var.alb_zone_id
    evaluate_target_health = true
  }
}

resource "aws_route53_record" "alb_wildcard" {
  count   = local.has_alb ? 1 : 0
  zone_id = aws_route53_zone.public[0].zone_id
  name    = "*.${var.domain_name}"
  type    = "A"

  alias {
    name                   = var.alb_dns_name
    zone_id                = var.alb_zone_id
    evaluate_target_health = true
  }
}

# ── Subdomain Records ────────────────────────────────────────────────────

resource "aws_route53_record" "subdomain" {
  for_each = var.subdomain_records

  zone_id = aws_route53_zone.public[0].zone_id
  name    = each.key
  type    = each.value.type
  ttl     = each.value.ttl
  records = each.value.records
}

# ── CDN Record (alias) ───────────────────────────────────────────────────

resource "aws_route53_record" "cdn" {
  count   = local.has_cdn ? 1 : 0
  zone_id = aws_route53_zone.public[0].zone_id
  name    = var.cdn_domain_name != "" ? "cdn.${var.domain_name}" : var.domain_name
  type    = "A"

  alias {
    name                   = var.cdn_domain_name
    zone_id                = var.cdn_hosted_zone_id
    evaluate_target_health = false
  }
}

# ── TXT Records ──────────────────────────────────────────────────────────

resource "aws_route53_record" "txt" {
  for_each = var.txt_records

  zone_id = aws_route53_zone.public[0].zone_id
  name    = each.key
  type    = "TXT"
  ttl     = each.value.ttl
  records = each.value.records
}

# ── MX Records ───────────────────────────────────────────────────────────

resource "aws_route53_record" "mx" {
  for_each = { for idx, mx in var.mx_records : idx => mx }

  zone_id = aws_route53_zone.public[0].zone_id
  name    = var.domain_name
  type    = "MX"
  ttl     = each.value.ttl

  records = [
    "${each.value.preference} ${each.value.hostname}"
  ]
}

# ── CNAME Records ────────────────────────────────────────────────────────

resource "aws_route53_record" "cname" {
  for_each = var.cname_records

  zone_id = aws_route53_zone.public[0].zone_id
  name    = each.key
  type    = "CNAME"
  ttl     = each.value.ttl
  records = [each.value.target]
}

# ── Health Checks ────────────────────────────────────────────────────────

resource "aws_route53_health_check" "this" {
  for_each = var.health_checks

  fqdn              = each.value.fqdn
  port              = each.value.port
  type              = each.value.type
  resource_path     = each.value.resource_path
  failure_threshold = each.value.failure_threshold
  request_interval  = each.value.request_interval

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-hc-${each.key}"
  })
}

# ── Failover Routing ─────────────────────────────────────────────────────

resource "aws_route53_record" "failover_primary" {
  count   = local.has_failover ? 1 : 0
  zone_id = aws_route53_zone.public[0].zone_id
  name    = var.domain_name
  type    = "A"

  set_identifier = "${var.name_prefix}-primary"

  failover_routing_policy {
    type = "PRIMARY"
  }

  health_check_id = var.primary_health_check_id != "" ? var.primary_health_check_id : null

  alias {
    name                   = var.primary_alb_dns_name
    zone_id                = var.primary_alb_zone_id
    evaluate_target_health = true
  }
}

resource "aws_route53_record" "failover_secondary" {
  count   = local.has_failover ? 1 : 0
  zone_id = aws_route53_zone.public[0].zone_id
  name    = var.domain_name
  type    = "A"

  set_identifier = "${var.name_prefix}-secondary"

  failover_routing_policy {
    type = "SECONDARY"
  }

  alias {
    name                   = var.secondary_alb_dns_name
    zone_id                = var.secondary_alb_zone_id
    evaluate_target_health = true
  }
}

# ── Latency-based Routing ────────────────────────────────────────────────

resource "aws_route53_record" "latency" {
  for_each = local.has_latency ? var.latency_records : {}

  zone_id = aws_route53_zone.public[0].zone_id
  name    = var.domain_name
  type    = "A"

  set_identifier = "${var.name_prefix}-${each.key}"

  latency_routing_policy {
    region = each.value.region
  }

  alias {
    name                   = each.value.dns_name
    zone_id                = each.value.zone_id
    evaluate_target_health = each.value.evaluate_target_health
  }
}

# ── NS Record for Subdomain Delegation ───────────────────────────────────

resource "aws_route53_record" "ns_delegation" {
  for_each = var.subdomain_records

  zone_id = aws_route53_zone.public[0].zone_id
  name    = each.key
  type    = "NS"
  ttl     = 172800
  records = each.value.records
}

# ── Private Zone Records ─────────────────────────────────────────────────

resource "aws_route53_record" "private_alb" {
  count   = local.has_private && local.has_alb ? 1 : 0
  zone_id = aws_route53_zone.private[0].zone_id
  name    = "app.internal.${var.domain_name}"
  type    = "A"

  alias {
    name                   = var.alb_dns_name
    zone_id                = var.alb_zone_id
    evaluate_target_health = true
  }
}
