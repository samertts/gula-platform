from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class TerraformSecurityConfig(BaseModel):
    backend_encryption: bool = True
    state_file_locking: bool = True
    remote_state_config: dict[str, Any] = Field(
        default_factory=lambda: {
            "backend": "s3",
            "bucket": "gula-terraform-state",
            "key": "terraform.tfstate",
            "region": "me-central-1",
            "encrypt": "true",
            "dynamodb_table": "terraform-state-lock",
        }
    )
    provider_version_validation: bool = True


class TerraformAuditFinding(BaseModel):
    resource_address: str
    rule_id: str
    severity: str
    description: str
    remediation: str
    line_number: int | None = None
