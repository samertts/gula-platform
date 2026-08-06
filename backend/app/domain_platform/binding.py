"""PROGRAM-STABLE-004 — Workspace Binding (Phase 6).

Each Domain binds to its own Workspace:

  Citizen Workspace      -> citizen_portal
  Laboratory Workspace   -> laboratory
  Pharmacy Workspace     -> pharmacy
  Radiology Workspace    -> radiology
  Hospital Workspace     -> hospital
  Blood Bank Workspace   -> blood_bank
  Public Health Workspace-> public_health
  Insurance Workspace    -> insurance

No Workspace may display another Domain's UI. The binding is enforced by
``assert_ui_allowed`` and by the identity WorkspaceService (ONE active
workspace per identity, permissions never cross workspaces).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.domain_platform.core import DOMAIN_WORKSPACE_TYPES
from app.domain_platform.manifest import CANONICAL_DOMAINS, workspace_ui_for


class WorkspaceBindingError(Exception):
    pass


@dataclass(frozen=True)
class WorkspaceBinding:
    """The binding of one Domain to one Workspace type."""

    domain_code: str
    workspace_type: str
    ui: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "domain_code": self.domain_code,
            "workspace_type": self.workspace_type,
            "ui": self.ui,
        }


class WorkspaceBindingRegistry:
    """The canonical Domain <-> Workspace binding map (Phase 6)."""

    def bindings(self) -> list[WorkspaceBinding]:
        return [
            WorkspaceBinding(
                domain_code=code,
                workspace_type=manifest.workspace_type,
                ui=manifest.ui,
            )
            for code, manifest in CANONICAL_DOMAINS.items()
        ]

    def binding_for_domain(self, domain_code: str) -> WorkspaceBinding | None:
        manifest = CANONICAL_DOMAINS.get(domain_code)
        if not manifest:
            return None
        return WorkspaceBinding(
            domain_code=domain_code,
            workspace_type=manifest.workspace_type,
            ui=manifest.ui,
        )

    def binding_for_workspace(self, workspace_type: str) -> WorkspaceBinding | None:
        for binding in self.bindings():
            if binding.workspace_type == workspace_type:
                return binding
        return None

    def domain_for_workspace(self, workspace_type: str) -> str | None:
        binding = self.binding_for_workspace(workspace_type)
        return binding.domain_code if binding else None

    def assert_domain_workspace(self, domain_code: str, workspace_type: str) -> None:
        expected = DOMAIN_WORKSPACE_TYPES.get(domain_code)
        if expected is not None and expected != workspace_type:
            raise WorkspaceBindingError(
                f"domain '{domain_code}' must bind to workspace type "
                f"'{expected}', not '{workspace_type}'"
            )

    def assert_ui_allowed(self, workspace_type: str, ui: str) -> None:
        """No Workspace may display another Domain's UI."""
        allowed = workspace_ui_for(workspace_type)
        if ui not in allowed:
            raise WorkspaceBindingError(
                f"workspace '{workspace_type}' may not display UI '{ui}'"
            )

    def assert_cross_workspace_ui_forbidden(self, workspace_type: str) -> None:
        """A Workspace must never render UI belonging to another Domain."""
        owned = workspace_ui_for(workspace_type)
        for _other_type, other_domain in DOMAIN_WORKSPACE_TYPES.items():
            other_ui = CANONICAL_DOMAINS[other_domain].ui if other_domain in CANONICAL_DOMAINS else []
            for ui in other_ui:
                if ui not in owned and ui in workspace_ui_for(workspace_type):
                    raise WorkspaceBindingError(
                        f"workspace '{workspace_type}' leaks UI '{ui}' from "
                        f"'{other_domain}'"
                    )
