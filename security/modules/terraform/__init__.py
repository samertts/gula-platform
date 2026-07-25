GSF-013: Terraform Module — Infrastructure policy-as-code.

Provides infrastructure security policy enforcement for the GULA platform
via Terraform policy-as-code. Integrates with OPA/Rego and Sentinel
to validate infrastructure configurations before deployment, detect
drift, and enforce security baselines across cloud and on-premises
environments.

Exports:
    TerraformSecurityEngine: Infrastructure security orchestration
    PolicyAsCodeEnforcer: Rego/Sentinel policy enforcement for Terraform
    DriftDetector: Infrastructure drift detection and alerting
    StateAnalyzer: Terraform state security analysis
    ModuleValidator: Terraform module security validation
    CloudIamAnalyzer: Cloud IAM configuration analysis
"""

from security.modules.terraform.engine import TerraformSecurityEngine
from security.modules.terraform.policy import PolicyAsCodeEnforcer
from security.modules.terraform.drift import DriftDetector
from security.modules.terraform.state import StateAnalyzer
from security.modules.terraform.modules import ModuleValidator
from security.modules.terraform.iam import CloudIamAnalyzer

__all__ = [
    "TerraformSecurityEngine",
    "PolicyAsCodeEnforcer",
    "DriftDetector",
    "StateAnalyzer",
    "ModuleValidator",
    "CloudIamAnalyzer",
]
