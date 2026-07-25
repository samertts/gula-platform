GSF-014: GitHub Module — Repository security posture.

Provides GitHub-specific security controls for the GULA platform
including repository security posture assessment, secret scanning,
branch protection policy enforcement, Dependabot configuration,
and GitHub Actions security hardening.

Exports:
    GitHubSecurityEngine: GitHub security orchestration
    RepoPostureAssessor: Repository security posture assessment
    SecretScanningIntegration: GitHub secret scanning integration
    BranchProtectionEnforcer: Branch protection policy enforcement
    DependabotConfigManager: Dependabot configuration management
    ActionsSecurityHardener: GitHub Actions security hardening
"""

from security.modules.github.engine import GitHubSecurityEngine
from security.modules.github.posture import RepoPostureAssessor
from security.modules.github.secrets import SecretScanningIntegration
from security.modules.github.branches import BranchProtectionEnforcer
from security.modules.github.dependabot import DependabotConfigManager
from security.modules.github.actions import ActionsSecurityHardener

__all__ = [
    "GitHubSecurityEngine",
    "RepoPostureAssessor",
    "SecretScanningIntegration",
    "BranchProtectionEnforcer",
    "DependabotConfigManager",
    "ActionsSecurityHardener",
]
