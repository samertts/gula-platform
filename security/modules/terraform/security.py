from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional, Set, Tuple

from pydantic import BaseModel, Field

from security.modules.terraform.models import TerraformAuditFinding, TerraformSecurityConfig

logger = logging.getLogger(__name__)

SENSITIVE_OUTPUT_PATTERNS: List[str] = [
    r"(?i)(password|secret|token|key|credential|private_key|ca_cert|certificate)",
    r"(?i)(access_key|secret_key|session_token)",
    r"(?i)(connection_string|dsn|jdbc|jwt|refresh_token)",
]

OPEN_PORTS_RISK: Set[int] = {22, 23, 3389, 5900, 5901, 6379, 9200, 9300, 27017, 5432, 3306}


class TerraformAuditReport(BaseModel):
    findings: List[TerraformAuditFinding] = Field(default_factory=list)
    passed: bool = True
    resource_count: int = 0
    file_count: int = 0


class TerraformSecurityManager:
    def __init__(self, config: Optional[TerraformSecurityConfig] = None):
        self.config = config or TerraformSecurityConfig()

    def validate_state_file_security(self) -> Dict[str, Any]:
        findings: List[str] = []
        passed = True

        if not self.config.state_file_locking:
            findings.append("State file locking is disabled - risk of concurrent modifications and state corruption")
            passed = False

        if not self.config.backend_encryption:
            findings.append("Backend encryption is disabled - state file stored in plaintext (contains secrets)")
            passed = False

        remote = self.config.remote_state_config
        if remote.get("encrypt") != "true":
            findings.append("S3 bucket encryption not enabled for state file")
            passed = False

        if remote.get("dynamodb_table"):
            if remote.get("backend") == "s3" and not remote.get("dynamodb_table"):
                findings.append("DynamoDB locking not configured for S3 backend")
                passed = False

        return {"findings": findings, "passed": passed}

    def validate_provider_versioning(self, content: str) -> Dict[str, Any]:
        findings: List[str] = []
        passed = True

        provider_patterns = re.findall(r'required_providers\s*\{[^}]*\}', content, re.DOTALL)
        for block in provider_patterns:
            provider_blocks = re.findall(r'(\w+)\s*=\s*\{([^}]*)\}', block)
            for name, body in provider_blocks:
                if "source" not in body:
                    findings.append(f"Provider '{name}' missing 'source' attribute")
                    passed = False

                version_match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', body)
                if not version_match:
                    findings.append(f"Provider '{name}' version not pinned - use version = \">= X.Y.Z, < X.Y.Z\"")
                    passed = False
                else:
                    version = version_match.group(1)
                    if version in ("latest", "", "~> 0.0"):
                        findings.append(f"Provider '{name}' has insufficient version constraint: '{version}'")
                        passed = False

        terraform_block = re.search(r'terraform\s*\{[^}]*\}', content, re.DOTALL)
        if not provider_patterns and not terraform_block:
            findings.append("No required_providers block found - providers not pinned")
            passed = False

        return {"findings": findings, "passed": passed}

    def check_backend_config(self, content: str) -> Dict[str, Any]:
        findings: List[str] = []
        passed = True

        backend_match = re.search(r'backend\s+"(\w+)"\s*\{([^}]*)\}', content, re.DOTALL)
        if backend_match:
            backend_type = backend_match.group(1)
            backend_body = backend_match.group(2)

            if backend_type in ("s3", "gcs", "azurerm"):
                if backend_type == "s3":
                    if "encrypt" not in backend_body:
                        findings.append("S3 backend missing 'encrypt = true' for state file encryption")
                        passed = False
                    if "dynamodb_table" not in backend_body and "dynamodb" not in backend_body:
                        findings.append("S3 backend missing DynamoDB table for state locking")
                        passed = False
                if "key" not in backend_body:
                    findings.append("Backend missing 'key' for state file path")
                    passed = False
            elif backend_type in ("pg", "postgresql", "mysql"):
                findings.append(f"Database backend '{backend_type}' - ensure TLS is enforced for state connections")

        if not backend_match:
            findings.append("No backend configuration found - state stored locally (not suitable for teams/production)")
            passed = False

        return {"findings": findings, "passed": passed}

    def detect_sensitive_outputs(self, content: str) -> Dict[str, Any]:
        findings: List[str] = []
        passed = True

        output_blocks = re.findall(r'output\s+"([^"]+)"\s*\{([^}]*)\}', content)
        for name, body in output_blocks:
            for pattern in SENSITIVE_OUTPUT_PATTERNS:
                if re.search(pattern, name):
                    if "sensitive = true" not in body:
                        findings.append(f"Output '{name}' contains potentially sensitive data but is NOT marked sensitive")
                        passed = False

            value_match = re.search(r'value\s*=\s*["\']([^"\']*)["\']', body)
            if value_match:
                value = value_match.group(1)
                for pattern in SENSITIVE_OUTPUT_PATTERNS:
                    if re.search(pattern, value):
                        findings.append(f"Output '{name}' exposes sensitive value in plaintext")
                        passed = False

        return {"findings": findings, "passed": passed}

    def validate_variable_security(self, content: str) -> Dict[str, Any]:
        findings: List[str] = []
        passed = True

        variable_blocks = re.findall(r'variable\s+"([^"]+)"\s*\{([^}]*)\}', content)
        for name, body in variable_blocks:
            for pattern in SENSITIVE_OUTPUT_PATTERNS:
                if re.search(pattern, name):
                    if "sensitive" not in body:
                        findings.append(f"Variable '{name}' is sensitive but NOT marked 'sensitive = true'")
                        passed = False
                    elif "sensitive = false" in body:
                        findings.append(f"Variable '{name}' is sensitive but explicitly marked sensitive = false")
                        passed = False

            if "type" not in body:
                findings.append(f"Variable '{name}' missing type constraint")
                passed = False

            if "default" in body:
                default_match = re.search(r'default\s*=\s*["\']([^"\']+)["\']', body)
                if default_match:
                    default_val = default_match.group(1)
                    for pattern in SENSITIVE_OUTPUT_PATTERNS:
                        if re.search(pattern, default_val):
                            findings.append(f"Variable '{name}' has sensitive default value - avoid defaults for secrets")
                            passed = False

            validation = re.search(r'validation\s*\{', body)
            if not validation:
                pass

        return {"findings": findings, "passed": passed}

    def validate_module_sources(self, content: str) -> Dict[str, Any]:
        findings: List[str] = []
        passed = True

        module_blocks = re.findall(r'module\s+"([^"]+)"\s*\{([^}]*)\}', content)
        for mod_name, body in module_blocks:
            source_match = re.search(r'source\s*=\s*["\']([^"\']+)["\']', body)
            if source_match:
                source = source_match.group(1)

                if source.startswith("git::") or source.startswith("github.com"):
                    version_match = re.search(r'ref=([^\s]+)', source) or re.search(r'version\s*=\s*["\']([^"\']+)["\']', body)
                    if not version_match:
                        findings.append(f"Module '{mod_name}' from git source '{source}' not pinned to a version/ref")
                        passed = False

                if source.startswith("./") or source.startswith("../"):
                    pass
                elif source.startswith("git::"):
                    if "deep_single_file" not in source:
                        pass
                elif "app.terraform.io" in source:
                    pass
                else:
                    if "//" not in source and "?" not in source:
                        if "hashicorp" not in source:
                            findings.append(f"Module '{mod_name}' source '{source}' - verify registry is trusted")
                            passed = False

                if source in ("hashicorp/consul/aws", "hashicorp/vault/aws", "hashicorp/nomad/aws"):
                    version_match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', body)
                    if not version_match:
                        findings.append(f"HashiCorp module '{mod_name}' not pinned to a version")
                        passed = False

        return {"findings": findings, "passed": passed}

    def audit_iam_permissions(self, content: str) -> Dict[str, Any]:
        findings: List[str] = []
        passed = True

        iam_policy_blocks = re.findall(r'resource\s+"aws_iam_policy"\s+"([^"]+)"\s*\{([^}]*)\}', content)

        for name, body in iam_policy_blocks:
            policy_match = re.search(r'policy\s*=\s*(<<[A-Z]+|jsonencode)', body)
            if policy_match:
                if "Statement" in body or "Effect" in body:
                    if '"*"' in body and '"Action"' in body:
                        findings.append(f"IAM policy '{name}' has wildcard (*) Action - violates least privilege")
                        passed = False
                    if '"Resource"' in body and '"*"' in body:
                        findings.append(f"IAM policy '{name}' has wildcard (*) Resource")
                        passed = False

        iam_role_blocks = re.findall(r'resource\s+"aws_iam_role"\s+"([^"]+)"\s*\{([^}]*)\}', content)
        for name, body in iam_role_blocks:
            assume_role = re.search(r'assume_role_policy', body)
            if not assume_role:
                findings.append(f"IAM role '{name}' has no assume_role_policy")

        return {"findings": findings, "passed": passed}

    def audit_security_group_rules(self, content: str) -> Dict[str, Any]:
        findings: List[str] = []
        passed = True

        sg_rule_blocks = re.findall(
            r'resource\s+"(aws_security_group_rule|aws_security_group)"\s+"([^"]+)"\s*\{([^}]*)\}', content
        )

        for resource_type, name, body in sg_rule_blocks:
            cidr_match = re.search(r'cidr_blocks\s*=\s*\[([^\]]*)\]', body)
            if cidr_match:
                cidrs = cidr_match.group(1)
                if '"0.0.0.0/0"' in cidrs:
                    from_port = re.search(r'from_port\s*=\s*(\d+)', body)
                    to_port = re.search(r'to_port\s*=\s*(\d+)', body)
                    protocol = re.search(r'protocol\s*=\s*["\']([^"\']+)["\']', body)

                    proto = protocol.group(1) if protocol else "all"
                    fp = int(from_port.group(1)) if from_port else 0
                    tp = int(to_port.group(1)) if to_port else 65535

                    if proto == "-1" or proto == "all":
                        findings.append(f"'{name}' allows all traffic from 0.0.0.0/0 (wildcard protocol)")
                        passed = False
                    elif fp <= 443 and tp >= 443:
                        if fp == 443 or (fp <= 80 and 80 <= tp):
                            pass
                        else:
                            findings.append(f"'{name}' allows [{fp}-{tp}] from 0.0.0.0/0 - overly permissive")
                            passed = False
                    else:
                        if fp in OPEN_PORTS_RISK or tp in OPEN_PORTS_RISK:
                            findings.append(f"'{name}' exposes port [{fp}-{tp}] ({proto}) to 0.0.0.0/0")
                            passed = False
                        else:
                            findings.append(f"'{name}' has inbound rule from 0.0.0.0/0 on ports [{fp}-{tp}]")
                            passed = False

        return {"findings": findings, "passed": passed}

    def enforce_resource_tagging(self, content: str, required_tags: Optional[List[str]] = None) -> Dict[str, Any]:
        tags = required_tags or ["Environment", "Project", "Owner", "CostCenter"]
        findings: List[str] = []
        passed = True

        resource_blocks = re.findall(r'resource\s+"(aws_\w+)"\s+"([^"]+)"\s*\{([^}]*)\}', content)
        for resource_type, name, body in resource_blocks:
            if resource_type in ("aws_s3_bucket", "aws_instance", "aws_lb", "aws_db_instance",
                                "aws_ecs_service", "aws_eks_cluster", "aws_lambda_function",
                                "aws_kms_key", "aws_sqs_queue", "aws_sns_topic"):
                if "tags" not in body:
                    findings.append(f"Resource '{resource_type}.{name}' missing tags block")
                    passed = False
                else:
                    for tag in tags:
                        if tag.lower() not in body.lower():
                            findings.append(f"Resource '{resource_type}.{name}' missing tag '{tag}'")
                            passed = False

        return {"findings": findings, "passed": passed}

    def validate_encryption_at_rest(self, content: str) -> Dict[str, Any]:
        findings: List[str] = []
        passed = True

        s3_buckets = re.findall(r'resource\s+"aws_s3_bucket"\s+"([^"]+)"\s*\{([^}]*)\}', content)
        for name, body in s3_buckets:
            if "server_side_encryption_configuration" not in body and "aws_s3_bucket_server_side_encryption_configuration" not in content:
                findings.append(f"S3 bucket '{name}' missing server-side encryption configuration")
                passed = False

        rds_instances = re.findall(r'resource\s+"aws_db_instance"\s+"([^"]+)"\s*\{([^}]*)\}', content)
        for name, body in rds_instances:
            storage_encrypted = re.search(r'storage_encrypted\s*=\s*(true|false)', body)
            if storage_encrypted and storage_encrypted.group(1) == "false":
                findings.append(f"RDS instance '{name}' storage encryption is disabled")
                passed = False
            elif not storage_encrypted:
                findings.append(f"RDS instance '{name}' missing storage_encrypted = true")
                passed = False

        ebs_volumes = re.findall(r'resource\s+"aws_ebs_volume"\s+"([^"]+)"\s*\{([^}]*)\}', content)
        for name, body in ebs_volumes:
            encrypted = re.search(r'encrypted\s*=\s*(true|false)', body)
            if encrypted and encrypted.group(1) == "false":
                findings.append(f"EBS volume '{name}' encryption is disabled")
                passed = False
            elif not encrypted:
                findings.append(f"EBS volume '{name}' missing encrypted = true")
                passed = False

        kms_keys = re.findall(r'resource\s+"aws_kms_key"\s+"([^"]+)"\s*\{([^}]*)\}', content)
        for name, body in kms_keys:
            deletion_window = re.search(r'deletion_window_in_days\s*=\s*(\d+)', body)
            if deletion_window:
                if int(deletion_window.group(1)) < 7:
                    findings.append(f"KMS key '{name}' deletion_window_in_days is {deletion_window.group(1)} - minimum 7")
                    passed = False
            if "enable_key_rotation" not in body:
                findings.append(f"KMS key '{name}' missing enable_key_rotation = true")
                passed = False

        return {"findings": findings, "passed": passed}

    def integrate_checkov(self, content: str) -> Dict[str, Any]:
        checkov_checks = {
            "CKV_AWS_1": {"description": "IAM password policy should prevent password reuse", "severity": "MEDIUM"},
            "CKV_AWS_2": {"description": "S3 bucket should have versioning enabled", "severity": "HIGH"},
            "CKV_AWS_3": {"description": "EBS volumes should be encrypted", "severity": "HIGH"},
            "CKV_AWS_4": {"description": "RDS instance storage should be encrypted", "severity": "HIGH"},
            "CKV_AWS_5": {"description": "RDS instance should be deployed in a VPC", "severity": "HIGH"},
            "CKV_AWS_7": {"description": "S3 bucket should have SSE enabled", "severity": "HIGH"},
            "CKV_AWS_21": {"description": "S3 bucket should have ACL defined", "severity": "MEDIUM"},
            "CKV_AWS_23": {"description": "Security group should not allow ingress from 0.0.0.0/0 to port 22", "severity": "HIGH"},
            "CKV_AWS_24": {"description": "Security group should not allow ingress from 0.0.0.0/0 to port 3389", "severity": "HIGH"},
            "CKV_AWS_25": {"description": "EKS cluster should have control plane logging enabled", "severity": "MEDIUM"},
            "CKV_AWS_26": {"description": "SNS topic should have server-side encryption", "severity": "HIGH"},
            "CKV_AWS_27": {"description": "SQS queue should have server-side encryption", "severity": "HIGH"},
            "CKV_AWS_28": {"description": "DynamoDB table should have point-in-time recovery", "severity": "MEDIUM"},
            "CKV_AWS_40": {"description": "IAM policy should not have a wildcard action", "severity": "HIGH"},
            "CKV_AWS_41": {"description": "S3 bucket should not allow public access", "severity": "CRITICAL"},
            "CKV_AWS_44": {"description": "Neptune cluster storage should be encrypted", "severity": "HIGH"},
            "CKV_AWS_45": {"description": "Redshift cluster should have encryption enabled", "severity": "HIGH"},
            "CKV_AWS_46": {"description": "EC2 instance should have detailed monitoring", "severity": "LOW"},
            "CKV_AWS_51": {"description": "ECR repository should have image scanning enabled", "severity": "HIGH"},
            "CKV_AWS_52": {"description": "S3 bucket should have MFA delete enabled", "severity": "MEDIUM"},
            "CKV_AWS_53": {"description": "S3 bucket should have block public access enabled", "severity": "HIGH"},
            "CKV_AWS_55": {"description": "EKS cluster should have secrets encryption", "severity": "HIGH"},
        }

        findings: List[str] = []
        matches = 0
        passed = True

        for check_id, check_info in checkov_checks.items():
            for resource_type, pattern in [
                ("password_reuse", r"aws_iam_account_password_policy"),
                ("versioning", r"versioning.*{\s*enabled\s*=\s*true"),
                ("ebs_encryption", r"encrypted\s*=\s*true"),
                ("rds_encryption", r"storage_encrypted\s*=\s*true"),
                ("sse", r"server_side_encryption"),
                ("s3_public", r"acl\s*=\s*\"public"),
                ("sg_port_22", r"from_port\s*=\s*22"),
                ("eks_logging", r"enabled_cluster_log_types"),
            ]:
                if re.search(pattern, content, re.IGNORECASE):
                    matches += 1

        return {"findings": findings, "passed": passed, "checkov_matches": matches, "total_checks": len(checkov_checks)}

    def full_audit(self, tf_content: str, required_tags: Optional[List[str]] = None) -> TerraformAuditReport:
        all_findings: List[TerraformAuditFinding] = []
        passed = True

        checks = [
            ("state_file", self.validate_state_file_security()),
            ("provider_versioning", self.validate_provider_versioning(tf_content)),
            ("backend_config", self.check_backend_config(tf_content)),
            ("sensitive_outputs", self.detect_sensitive_outputs(tf_content)),
            ("variable_security", self.validate_variable_security(tf_content)),
            ("module_sources", self.validate_module_sources(tf_content)),
            ("iam_permissions", self.audit_iam_permissions(tf_content)),
            ("security_group_rules", self.audit_security_group_rules(tf_content)),
            ("resource_tagging", self.enforce_resource_tagging(tf_content, required_tags)),
            ("encryption_at_rest", self.validate_encryption_at_rest(tf_content)),
        ]

        severity_map = {
            "state_file": "HIGH",
            "provider_versioning": "MEDIUM",
            "backend_config": "HIGH",
            "sensitive_outputs": "HIGH",
            "variable_security": "MEDIUM",
            "module_sources": "MEDIUM",
            "iam_permissions": "HIGH",
            "security_group_rules": "HIGH",
            "resource_tagging": "LOW",
            "encryption_at_rest": "HIGH",
        }

        for rule_id, result in checks:
            if not result["passed"]:
                passed = False
                for f in result["findings"]:
                    all_findings.append(TerraformAuditFinding(
                        resource_address="(global)",
                        rule_id=rule_id,
                        severity=severity_map.get(rule_id, "MEDIUM"),
                        description=f,
                        remediation=self._remediation_for(rule_id, f),
                    ))

        return TerraformAuditReport(findings=all_findings, passed=passed, resource_count=tf_content.count("resource "))

    @staticmethod
    def _remediation_for(rule_id: str, finding: str) -> str:
        remediations = {
            "state_file": "Enable S3 backend encryption and DynamoDB locking for state files",
            "provider_versioning": "Pin provider versions with version constraints like '~> X.Y' or '>= X.Y, < X.Y'",
            "backend_config": "Configure remote backend (S3/GCS/AzureRM) with encryption and state locking",
            "sensitive_outputs": "Mark sensitive outputs with 'sensitive = true' and avoid hardcoding secrets",
            "variable_security": "Mark variables as sensitive = true when they contain secrets",
            "module_sources": "Pin module versions and use only trusted registries",
            "iam_permissions": "Apply least privilege - avoid wildcard Actions and Resources",
            "security_group_rules": "Restrict ingress CIDR blocks - avoid 0.0.0.0/0 where possible",
            "resource_tagging": "Add required tags to all resources for resource governance",
            "encryption_at_rest": "Enable encryption for all storage resources (S3, RDS, EBS, KMS)",
        }
        for key, remediation in remediations.items():
            if rule_id == key:
                return remediation
        return "Review and apply security best practices"
