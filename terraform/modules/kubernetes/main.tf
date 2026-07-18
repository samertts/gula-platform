locals {
  cluster_name = var.name_prefix
}

data "aws_caller_identity" "current" {}

# ── CloudWatch Log Group ─────────────────────────────────────────────────

resource "aws_cloudwatch_log_group" "eks" {
  name              = "/aws/eks/${local.cluster_name}/cluster"
  retention_in_days = var.log_retention_days

  tags = merge(var.tags, {
    Name = "${local.cluster_name}-eks-logs"
  })
}

# ── IAM Role for EKS Cluster ─────────────────────────────────────────────

resource "aws_iam_role" "cluster" {
  name               = "${local.cluster_name}-eks-cluster"
  assume_role_policy = data.aws_iam_policy_document.cluster_assume.json

  tags = merge(var.tags, {
    Name = "${local.cluster_name}-eks-cluster-role"
  })
}

data "aws_iam_policy_document" "cluster_assume" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["eks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role_policy_attachment" "cluster_policy" {
  role       = aws_iam_role.cluster.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
}

resource "aws_iam_role_policy_attachment" "service_policy" {
  role       = aws_iam_role.cluster.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSServicePolicy"
}

resource "aws_iam_role_policy_attachment" "vpc_resource_controller" {
  role       = aws_iam_role.cluster.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSVPCResourceController"
}

# ── EKS Cluster ──────────────────────────────────────────────────────────

resource "aws_eks_cluster" "this" {
  name     = local.cluster_name
  role_arn = aws_iam_role.cluster.arn
  version  = var.cluster_version

  vpc_config {
    subnet_ids              = var.subnet_ids
    endpoint_private_access = true
    endpoint_public_access  = false
    public_access_cidrs     = []
    security_group_ids      = [aws_security_group.cluster.id]
  }

  enabled_cluster_log_types = var.cluster_log_types

  encryption_config {
    provider {
      key_arn = var.kms_key_arn != "" ? var.kms_key_arn : aws_kms_key.eks[0].arn
    }
    resources = ["secrets"]
  }

  tags = merge(var.tags, {
    Name = local.cluster_name
  })

  depends_on = [
    aws_iam_role_policy_attachment.cluster_policy,
    aws_iam_role_policy_attachment.service_policy,
    aws_iam_role_policy_attachment.vpc_resource_controller,
    aws_cloudwatch_log_group.eks,
  ]
}

resource "aws_kms_key" "eks" {
  count                 = var.kms_key_arn != "" ? 0 : 1
  description           = "EKS secrets encryption key for ${local.cluster_name}"
  deletion_window_in_days = 30
  enable_key_rotation   = true

  tags = merge(var.tags, {
    Name = "${local.cluster_name}-eks-kms"
  })
}

# ── Security Groups ──────────────────────────────────────────────────────

resource "aws_security_group" "cluster" {
  name_prefix = "${local.cluster_name}-eks-cluster-"
  description = "EKS cluster security group"
  vpc_id      = var.vpc_id

  egress {
    description = "All outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, {
    Name = "${local.cluster_name}-eks-cluster-sg"
  })
}

resource "aws_security_group" "node" {
  name_prefix = "${local.cluster_name}-eks-node-"
  description = "EKS node security group"
  vpc_id      = var.vpc_id

  ingress {
    description     = "Cluster to node communication"
    from_port       = 0
    to_port         = 0
    protocol        = "-1"
    security_groups = [aws_security_group.cluster.id]
  }

  ingress {
    description = "Node to node communication"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    self        = true
  }

  ingress {
    description = "Metrics scraping"
    from_port   = 9100
    to_port     = 9100
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "All outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, {
    Name = "${local.cluster_name}-eks-node-sg"
  })
}

# ── OIDC Provider ────────────────────────────────────────────────────────

data "tls_certificate" "eks" {
  url = aws_eks_cluster.this.identity[0].oidc[0].issuer
}

resource "aws_iam_openid_connect_provider" "this" {
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = [data.tls_certificate.eks.certificates[0].sha1_fingerprint]
  url             = aws_eks_cluster.this.identity[0].oidc[0].issuer

  tags = merge(var.tags, {
    Name = "${local.cluster_name}-oidc"
  })
}

# ── IAM Role for Nodes ───────────────────────────────────────────────────

resource "aws_iam_role" "node" {
  name               = "${local.cluster_name}-eks-node"
  assume_role_policy = data.aws_iam_policy_document.node_assume.json

  tags = merge(var.tags, {
    Name = "${local.cluster_name}-eks-node-role"
  })
}

data "aws_iam_policy_document" "node_assume" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role_policy_attachment" "node_worker" {
  role       = aws_iam_role.node.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy"
}

resource "aws_iam_role_policy_attachment" "node_cni" {
  role       = aws_iam_role.node.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy"
}

resource "aws_iam_role_policy_attachment" "node_ecr" {
  role       = aws_iam_role.node.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
}

resource "aws_iam_role_policy_attachment" "node_ssm" {
  role       = aws_iam_role.node.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

# Additional node policy for EBS CSI and CloudWatch
resource "aws_iam_role_policy" "node_additional" {
  name   = "${local.cluster_name}-eks-node-additional"
  role   = aws_iam_role.node.name
  policy = data.aws_iam_policy_document.node_additional.json
}

data "aws_iam_policy_document" "node_additional" {
  statement {
    sid    = "EBS"
    effect = "Allow"
    actions = [
      "ec2:AttachVolume",
      "ec2:CreateSnapshot",
      "ec2:CreateTags",
      "ec2:CreateVolume",
      "ec2:DeleteSnapshot",
      "ec2:DeleteTags",
      "ec2:DeleteVolume",
      "ec2:DescribeInstances",
      "ec2:DescribeSnapshots",
      "ec2:DescribeTags",
      "ec2:DescribeVolumes",
      "ec2:DescribeVolumesModifications",
      "ec2:DetachVolume",
      "ec2:ModifyVolume",
    ]
    resources = ["*"]
  }

  statement {
    sid    = "CloudWatch"
    effect = "Allow"
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:DescribeLogGroups",
      "logs:DescribeLogStreams",
      "logs:PutLogEvents",
      "cloudwatch:PutMetricData",
    ]
    resources = ["*"]
  }
}

# ── VPC CNI IAM Role (IRSA) ──────────────────────────────────────────────

resource "aws_iam_role" "vpc_cni" {
  name               = "${local.cluster_name}-vpc-cni"
  assume_role_policy = data.aws_iam_policy_document.irsa_assume.json

  tags = merge(var.tags, {
    Name = "${local.cluster_name}-vpc-cni-role"
  })
}

data "aws_iam_policy_document" "irsa_assume" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]
    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.this.arn]
    }
    condition {
      test     = "StringEquals"
      variable = "${replace(aws_iam_openid_connect_provider.this.url, "https://", "")}:sub"
      values   = ["system:serviceaccount:kube-system:aws-node"]
    }
  }
}

resource "aws_iam_role_policy_attachment" "vpc_cni" {
  role       = aws_iam_role.vpc_cni.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy"
}

# ── Cluster Autoscaler IAM Role (IRSA) ───────────────────────────────────

resource "aws_iam_role" "cluster_autoscaler" {
  count              = var.cluster_autoscaler_enabled ? 1 : 0
  name               = "${local.cluster_name}-cluster-autoscaler"
  assume_role_policy = data.aws_iam_policy_document.cluster_autoscaler_assume[0].json

  tags = merge(var.tags, {
    Name = "${local.cluster_name}-cluster-autoscaler-role"
  })
}

data "aws_iam_policy_document" "cluster_autoscaler_assume" {
  count = var.cluster_autoscaler_enabled ? 1 : 0

  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]
    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.this.arn]
    }
    condition {
      test     = "StringEquals"
      variable = "${replace(aws_iam_openid_connect_provider.this.url, "https://", "")}:sub"
      values   = ["system:serviceaccount:kube-system:cluster-autoscaler"]
    }
  }
}

resource "aws_iam_role_policy" "cluster_autoscaler" {
  count  = var.cluster_autoscaler_enabled ? 1 : 0
  name   = "${local.cluster_name}-cluster-autoscaler"
  role   = aws_iam_role.cluster_autoscaler[0].name
  policy = data.aws_iam_policy_document.cluster_autoscaler_policy[0].json
}

data "aws_iam_policy_document" "cluster_autoscaler_policy" {
  count = var.cluster_autoscaler_enabled ? 1 : 0

  statement {
    sid    = "Autoscaling"
    effect = "Allow"
    actions = [
      "autoscaling:DescribeAutoScalingGroups",
      "autoscaling:DescribeAutoScalingInstances",
      "autoscaling:DescribeLaunchConfigurations",
      "autoscaling:DescribeScalingActivities",
      "autoscaling:DescribeTags",
      "autoscaling:SetDesiredCapacity",
      "autoscaling:TerminateInstanceInAutoScalingGroup",
      "ec2:DescribeInstanceTypes",
      "ec2:DescribeLaunchTemplateVersions",
      "ec2:DescribeImages",
      "ec2:GetInstanceTypesFromInstanceRequirements",
      "eks:DescribeNodegroup",
    ]
    resources = ["*"]
  }
}

# ── Node Termination Handler IAM Role (IRSA) ─────────────────────────────

resource "aws_iam_role" "node_termination_handler" {
  count              = var.node_termination_handler_enabled ? 1 : 0
  name               = "${local.cluster_name}-node-termination-handler"
  assume_role_policy = data.aws_iam_policy_document.node_termination_handler_assume[0].json

  tags = merge(var.tags, {
    Name = "${local.cluster_name}-node-termination-handler-role"
  })
}

data "aws_iam_policy_document" "node_termination_handler_assume" {
  count = var.node_termination_handler_enabled ? 1 : 0

  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]
    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.this.arn]
    }
    condition {
      test     = "StringEquals"
      variable = "${replace(aws_iam_openid_connect_provider.this.url, "https://", "")}:sub"
      values   = ["system:serviceaccount:kube-system:aws-node-termination-handler"]
    }
  }
}

resource "aws_iam_role_policy" "node_termination_handler" {
  count  = var.node_termination_handler_enabled ? 1 : 0
  name   = "${local.cluster_name}-node-termination-handler"
  role   = aws_iam_role.node_termination_handler[0].name
  policy = data.aws_iam_policy_document.node_termination_handler_policy[0].json
}

data "aws_iam_policy_document" "node_termination_handler_policy" {
  count = var.node_termination_handler_enabled ? 1 : 0

  statement {
    sid    = "EC2"
    effect = "Allow"
    actions = [
      "autoscaling:DescribeAutoScalingInstances",
      "autoscaling:DescribeTags",
      "ec2:DescribeInstances",
      "ec2:DescribeInstanceTypes",
      "ec2:DescribeSpotInstanceRequests",
    ]
    resources = ["*"]
  }

  statement {
    sid    = "SQS"
    effect = "Allow"
    actions = [
      "sqs:ReceiveMessage",
      "sqs:DeleteMessage",
      "sqs:GetQueueUrl",
      "sqs:GetQueueAttributes",
    ]
    resources = ["arn:aws:sqs:*:*:${local.cluster_name}-*"]
  }
}

# ── Managed Node Groups ──────────────────────────────────────────────────

resource "aws_eks_node_group" "system" {
  cluster_name    = aws_eks_cluster.this.name
  node_group_name = "${local.cluster_name}-system"
  node_role_arn   = aws_iam_role.node.arn
  subnet_ids      = var.subnet_ids
  version         = var.cluster_version
  release_version = null

  instance_types = [var.instance_types.system]

  scaling_config {
    min_size     = var.node_group_config.system_min_size
    max_size     = var.node_group_config.system_max_size
    desired_size = var.node_group_config.system_desired_size
  }

  update_config {
    max_unavailable = 1
  }

  capacity_type = "ON_DEMAND"
  disk_size     = 50

  labels = {
    "nodegroup-type"    = "system"
    "gula.io/node-pool" = "system"
  }

  tags = merge(var.tags, {
    Name                                         = "${local.cluster_name}-system"
    "k8s.io/cluster-autoscaler/${local.cluster_name}" = "owned"
    "k8s.io/cluster-autoscaler/enabled"               = "true"
  })

  depends_on = [
    aws_iam_role_policy_attachment.node_worker,
    aws_iam_role_policy_attachment.node_cni,
    aws_iam_role_policy_attachment.node_ecr,
  ]

  lifecycle {
    create_before_destroy = true
    ignore_changes        = [scaling_config[0].desired_size, release_version]
  }
}

resource "aws_eks_node_group" "application" {
  cluster_name    = aws_eks_cluster.this.name
  node_group_name = "${local.cluster_name}-application"
  node_role_arn   = aws_iam_role.node.arn
  subnet_ids      = var.subnet_ids
  version         = var.cluster_version
  release_version = null

  instance_types = [var.instance_types.application]

  scaling_config {
    min_size     = var.node_group_config.app_min_size
    max_size     = var.node_group_config.app_max_size
    desired_size = var.node_group_config.app_desired_size
  }

  update_config {
    max_unavailable = 1
  }

  capacity_type = "ON_DEMAND"
  disk_size     = 100

  labels = {
    "nodegroup-type"    = "application"
    "gula.io/node-pool" = "application"
  }

  tags = merge(var.tags, {
    Name                                         = "${local.cluster_name}-application"
    "k8s.io/cluster-autoscaler/${local.cluster_name}" = "owned"
    "k8s.io/cluster-autoscaler/enabled"               = "true"
  })

  lifecycle {
    create_before_destroy = true
    ignore_changes        = [scaling_config[0].desired_size, release_version]
  }
}

resource "aws_eks_node_group" "spot" {
  count           = var.node_group_config.spot_max_size > 0 ? 1 : 0
  cluster_name    = aws_eks_cluster.this.name
  node_group_name = "${local.cluster_name}-spot"
  node_role_arn   = aws_iam_role.node.arn
  subnet_ids      = var.subnet_ids
  version         = var.cluster_version
  release_version = null

  instance_types = [var.instance_types.spot]

  scaling_config {
    min_size     = var.node_group_config.spot_min_size
    max_size     = var.node_group_config.spot_max_size
    desired_size = var.node_group_config.spot_desired_size
  }

  update_config {
    max_unavailable = 1
  }

  capacity_type = "SPOT"
  disk_size     = 100

  labels = {
    "nodegroup-type"    = "spot"
    "gula.io/node-pool" = "spot"
    "lifecycle"         = "Ec2Spot"
  }

  tags = merge(var.tags, {
    Name                                         = "${local.cluster_name}-spot"
    "k8s.io/cluster-autoscaler/${local.cluster_name}" = "owned"
    "k8s.io/cluster-autoscaler/enabled"               = "true"
  })

  lifecycle {
    create_before_destroy = true
    ignore_changes        = [scaling_config[0].desired_size, release_version]
  }
}

# ── EBS CSI Driver IAM Role (IRSA) ───────────────────────────────────────

resource "aws_iam_role" "ebs_csi" {
  name               = "${local.cluster_name}-ebs-csi"
  assume_role_policy = data.aws_iam_policy_document.ebs_csi_assume.json

  tags = merge(var.tags, {
    Name = "${local.cluster_name}-ebs-csi-role"
  })
}

data "aws_iam_policy_document" "ebs_csi_assume" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]
    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.this.arn]
    }
    condition {
      test     = "StringEquals"
      variable = "${replace(aws_iam_openid_connect_provider.this.url, "https://", "")}:sub"
      values   = ["system:serviceaccount:kube-system:ebs-csi-controller-sa"]
    }
  }
}

resource "aws_iam_role_policy_attachment" "ebs_csi" {
  role       = aws_iam_role.ebs_csi.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy"
}

# ── EKS Add-ons ─────────────────────────────────────────────────────────

resource "aws_eks_addon" "vpc_cni" {
  cluster_name                = aws_eks_cluster.this.name
  addon_name                  = "vpc-cni"
  addon_version               = null
  service_account_role_arn    = aws_iam_role.vpc_cni.arn
  resolve_conflicts_on_update = "PRESERVE"

  depends_on = [aws_eks_node_group.system]
}

resource "aws_eks_addon" "coredns" {
  cluster_name                = aws_eks_cluster.this.name
  addon_name                  = "coredns"
  addon_version               = null
  resolve_conflicts_on_update = "PRESERVE"

  depends_on = [aws_eks_node_group.system]
}

resource "aws_eks_addon" "kube_proxy" {
  cluster_name                = aws_eks_cluster.this.name
  addon_name                  = "kube-proxy"
  addon_version               = null
  resolve_conflicts_on_update = "PRESERVE"

  depends_on = [aws_eks_node_group.system]
}

resource "aws_eks_addon" "ebs_csi" {
  cluster_name                = aws_eks_cluster.this.name
  addon_name                  = "aws-ebs-csi-driver"
  addon_version               = null
  service_account_role_arn    = aws_iam_role.ebs_csi.arn
  resolve_conflicts_on_update = "PRESERVE"

  depends_on = [aws_eks_node_group.system]
}
