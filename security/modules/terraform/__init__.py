"""
GSF-005: Terraform Security Module — IaC security analysis.

Exports:
    TerraformSecurityConfig: Terraform security configuration model
    TerraformAuditFinding: Terraform audit finding model
    TerraformSecurityManager: Terraform security analysis and enforcement
"""

from security.modules.terraform.models import TerraformAuditFinding, TerraformSecurityConfig
from security.modules.terraform.security import TerraformSecurityManager

__all__ = [
    "TerraformAuditFinding",
    "TerraformSecurityConfig",
    "TerraformSecurityManager",
]
