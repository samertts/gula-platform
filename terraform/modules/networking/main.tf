locals {
  az_count = length(var.availability_zones)
}

resource "aws_vpc" "this" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-vpc"
  })
}

# ── Internet Gateway ────────────────────────────────────────────────────

resource "aws_internet_gateway" "this" {
  vpc_id = aws_vpc.this.id

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-igw"
  })
}

# ── Public Subnets ──────────────────────────────────────────────────────

resource "aws_subnet" "public" {
  count = local.az_count

  vpc_id                  = aws_vpc.this.id
  cidr_block              = var.public_subnet_cidrs[count.index]
  availability_zone       = var.availability_zones[count.index]
  map_public_ip_on_launch = true

  tags = merge(var.tags, {
    Name                                          = "${var.name_prefix}-public-${count.index + 1}"
    "kubernetes.io/role/elb"                      = "1"
    "kubernetes.io/cluster/${var.name_prefix}"    = "shared"
  })
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.this.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.this.id
  }

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-public-rt"
  })
}

resource "aws_route_table_association" "public" {
  count = local.az_count

  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# ── NAT Gateways ────────────────────────────────────────────────────────

resource "aws_eip" "nat" {
  count = var.single_nat_gateway ? 1 : local.az_count
  domain = "vpc"

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-nat-eip-${count.index + 1}"
  })
}

resource "aws_nat_gateway" "this" {
  count = var.enable_nat_gateway ? (var.single_nat_gateway ? 1 : local.az_count) : 0

  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[var.single_nat_gateway ? 0 : count.index].id

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-nat-${count.index + 1}"
  })

  depends_on = [aws_internet_gateway.this]
}

# ── Private Subnets ─────────────────────────────────────────────────────

resource "aws_subnet" "private" {
  count = local.az_count

  vpc_id                  = aws_vpc.this.id
  cidr_block              = var.private_subnet_cidrs[count.index]
  availability_zone       = var.availability_zones[count.index]
  map_public_ip_on_launch = false

  tags = merge(var.tags, {
    Name                                          = "${var.name_prefix}-private-${count.index + 1}"
    "kubernetes.io/role/internal-elb"             = "1"
    "kubernetes.io/cluster/${var.name_prefix}"    = "shared"
  })
}

resource "aws_route_table" "private" {
  count = var.enable_nat_gateway ? local.az_count : 0

  vpc_id = aws_vpc.this.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = var.single_nat_gateway ? aws_nat_gateway.this[0].id : aws_nat_gateway.this[count.index].id
  }

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-private-rt-${count.index + 1}"
  })
}

resource "aws_route_table_association" "private" {
  count = var.enable_nat_gateway ? local.az_count : 0

  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private[count.index].id
}

# ── Database Subnets ────────────────────────────────────────────────────

resource "aws_subnet" "database" {
  count = local.az_count

  vpc_id                  = aws_vpc.this.id
  cidr_block              = var.database_subnet_cidrs[count.index]
  availability_zone       = var.availability_zones[count.index]
  map_public_ip_on_launch = false

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-database-${count.index + 1}"
  })
}

resource "aws_db_subnet_group" "this" {
  name       = "${var.name_prefix}-db-subnet-group"
  subnet_ids = aws_subnet.database[*].id

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-db-subnet-group"
  })
}

resource "aws_route_table" "database" {
  count = var.enable_nat_gateway ? local.az_count : 0

  vpc_id = aws_vpc.this.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = var.single_nat_gateway ? aws_nat_gateway.this[0].id : aws_nat_gateway.this[count.index].id
  }

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-database-rt-${count.index + 1}"
  })
}

resource "aws_route_table_association" "database" {
  count = var.enable_nat_gateway ? local.az_count : 0

  subnet_id      = aws_subnet.database[count.index].id
  route_table_id = aws_route_table.database[count.index].id
}

# ── ElastiCache Subnets ─────────────────────────────────────────────────

resource "aws_subnet" "elasticache" {
  count = local.az_count

  vpc_id                  = aws_vpc.this.id
  cidr_block              = var.elasticache_subnet_cidrs[count.index]
  availability_zone       = var.availability_zones[count.index]
  map_public_ip_on_launch = false

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-elasticache-${count.index + 1}"
  })
}

resource "aws_elasticache_subnet_group" "this" {
  name       = "${var.name_prefix}-elasticache-subnet-group"
  subnet_ids = aws_subnet.elasticache[*].id

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-elasticache-subnet-group"
  })
}

# ── VPC Endpoints ───────────────────────────────────────────────────────

data "aws_vpc_endpoint_service" "s3" {
  count  = var.enable_vpc_endpoints ? 1 : 0
  service = "s3"
}

data "aws_vpc_endpoint_service" "dynamodb" {
  count  = var.enable_vpc_endpoints ? 1 : 0
  service = "dynamodb"
}

data "aws_vpc_endpoint_service" "ecr_api" {
  count  = var.enable_vpc_endpoints ? 1 : 0
  service = "ecr.api"
}

data "aws_vpc_endpoint_service" "ecr_dkr" {
  count  = var.enable_vpc_endpoints ? 1 : 0
  service = "ecr.dkr"
}

data "aws_vpc_endpoint_service" "ec2" {
  count  = var.enable_vpc_endpoints ? 1 : 0
  service = "ec2"
}

data "aws_vpc_endpoint_service" "logs" {
  count  = var.enable_vpc_endpoints ? 1 : 0
  service = "logs"
}

data "aws_vpc_endpoint_service" "monitoring" {
  count  = var.enable_vpc_endpoints ? 1 : 0
  service = "monitoring"
}

data "aws_vpc_endpoint_service" "secretsmanager" {
  count  = var.enable_vpc_endpoints ? 1 : 0
  service = "secretsmanager"
}

resource "aws_vpc_endpoint" "s3" {
  count  = var.enable_vpc_endpoints ? 1 : 0
  vpc_id       = aws_vpc.this.id
  service_name = data.aws_vpc_endpoint_service.s3[0].service_name

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-s3-endpoint"
  })
}

resource "aws_vpc_endpoint" "dynamodb" {
  count  = var.enable_vpc_endpoints ? 1 : 0
  vpc_id       = aws_vpc.this.id
  service_name = data.aws_vpc_endpoint_service.dynamodb[0].service_name

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-dynamodb-endpoint"
  })
}

resource "aws_vpc_endpoint" "interface" {
  for_each = var.enable_vpc_endpoints ? {
    ecr_api       = data.aws_vpc_endpoint_service.ecr_api[0].service_name
    ecr_dkr       = data.aws_vpc_endpoint_service.ecr_dkr[0].service_name
    ec2           = data.aws_vpc_endpoint_service.ec2[0].service_name
    logs          = data.aws_vpc_endpoint_service.logs[0].service_name
    monitoring    = data.aws_vpc_endpoint_service.monitoring[0].service_name
    secretsmanager = data.aws_vpc_endpoint_service.secretsmanager[0].service_name
  } : {}

  vpc_id             = aws_vpc.this.id
  service_name       = each.value
  vpc_endpoint_type  = "Interface"
  subnet_ids         = aws_subnet.private[*].id
  security_group_ids = [aws_security_group.vpc_endpoints.id]
  private_dns_enabled = true

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-${each.key}-endpoint"
  })
}

# ── Security Groups ─────────────────────────────────────────────────────

resource "aws_security_group" "vpc_endpoints" {
  name_prefix = "${var.name_prefix}-vpc-endpoints-"
  description = "Security group for VPC endpoints"
  vpc_id      = aws_vpc.this.id

  ingress {
    description = "HTTPS from VPC"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-vpc-endpoints-sg"
  })
}

resource "aws_security_group" "alb" {
  name_prefix = "${var.name_prefix}-alb-"
  description = "Security group for ALB"
  vpc_id      = aws_vpc.this.id

  ingress {
    description = "HTTP from internet"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS from internet"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "All traffic to VPC"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = [var.vpc_cidr]
  }

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-alb-sg"
  })
}

resource "aws_security_group" "app" {
  name_prefix = "${var.name_prefix}-app-"
  description = "Security group for application instances"
  vpc_id      = aws_vpc.this.id

  ingress {
    description = "App traffic from ALB"
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  ingress {
    description = "Node metrics scraping"
    from_port   = 9100
    to_port     = 9100
    protocol    = "tcp"
    cidr_blocks = var.vpc_cidr != null ? [var.vpc_cidr] : []
  }

  egress {
    description = "All outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-app-sg"
  })
}

resource "aws_security_group" "database" {
  name_prefix = "${var.name_prefix}-database-"
  description = "Security group for database instances"
  vpc_id      = aws_vpc.this.id

  ingress {
    description = "PostgreSQL from app"
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    security_groups = [aws_security_group.app.id]
  }

  ingress {
    description = "PgBouncer from app"
    from_port   = 6432
    to_port     = 6432
    protocol    = "tcp"
    security_groups = [aws_security_group.app.id]
  }

  ingress {
    description = "Patroni REST API"
    from_port   = 8008
    to_port     = 8008
    protocol    = "tcp"
    security_groups = [aws_security_group.app.id]
  }

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-database-sg"
  })
}

resource "aws_security_group" "cache" {
  name_prefix = "${var.name_prefix}-cache-"
  description = "Security group for cache instances"
  vpc_id      = aws_vpc.this.id

  ingress {
    description = "Redis from app"
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
    security_groups = [aws_security_group.app.id]
  }

  ingress {
    description = "Redis sentinel"
    from_port   = 26379
    to_port     = 26379
    protocol    = "tcp"
    security_groups = [aws_security_group.app.id]
  }

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-cache-sg"
  })
}

resource "aws_security_group" "rabbitmq" {
  name_prefix = "${var.name_prefix}-rabbitmq-"
  description = "Security group for RabbitMQ"
  vpc_id      = aws_vpc.this.id

  ingress {
    description = "AMQP from app"
    from_port   = 5672
    to_port     = 5672
    protocol    = "tcp"
    security_groups = [aws_security_group.app.id]
  }

  ingress {
    description = "AMQPS from app"
    from_port   = 5671
    to_port     = 5671
    protocol    = "tcp"
    security_groups = [aws_security_group.app.id]
  }

  ingress {
    description = "Management UI"
    from_port   = 15672
    to_port     = 15672
    protocol    = "tcp"
    security_groups = [aws_security_group.app.id]
  }

  ingress {
    description = "Erlang distribution"
    from_port   = 4369
    to_port     = 4369
    protocol    = "tcp"
    security_groups = [aws_security_group.app.id]
  }

  ingress {
    description = "Erlang clustering"
    from_port   = 25672
    to_port     = 25672
    protocol    = "tcp"
    self        = true
  }

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-rabbitmq-sg"
  })
}

# ── VPC Flow Logs ───────────────────────────────────────────────────────

resource "aws_flow_log" "this" {
  count = var.enable_flow_logs ? 1 : 0

  log_destination_type     = "cloud-watch-logs"
  log_destination          = aws_cloudwatch_log_group.flow_logs[0].arn
  traffic_type             = "ALL"
  vpc_id                   = aws_vpc.this.id
  iam_role_arn             = aws_iam_role.flow_logs[0].arn

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-flow-log"
  })
}

resource "aws_cloudwatch_log_group" "flow_logs" {
  count = var.enable_flow_logs ? 1 : 0

  name              = "/aws/vpc/flow-logs/${var.name_prefix}"
  retention_in_days = var.log_retention_days

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-flow-logs"
  })
}

resource "aws_iam_role" "flow_logs" {
  count = var.enable_flow_logs ? 1 : 0

  name               = "${var.name_prefix}-flow-logs-role"
  assume_role_policy = data.aws_iam_policy_document.flow_logs_assume[0].json

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-flow-logs-role"
  })
}

data "aws_iam_policy_document" "flow_logs_assume" {
  count = var.enable_flow_logs ? 1 : 0

  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["vpc-flow-logs.amazonaws.com"]
    }
  }
}

resource "aws_iam_role_policy" "flow_logs" {
  count = var.enable_flow_logs ? 1 : 0

  name   = "${var.name_prefix}-flow-logs-policy"
  role   = aws_iam_role.flow_logs[0].id
  policy = data.aws_iam_policy_document.flow_logs_policy[0].json
}

data "aws_iam_policy_document" "flow_logs_policy" {
  count = var.enable_flow_logs ? 1 : 0

  statement {
    effect = "Allow"
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
      "logs:DescribeLogGroups",
      "logs:DescribeLogStreams",
    ]
    resources = ["*"]
  }
}
