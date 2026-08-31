"""Server-authoritative ABO/Rh compatibility policy.

Malformed or incomplete blood groups are indeterminate, never silently
converted to O-negative. The policy version is returned with every decision.
"""
from __future__ import annotations

from typing import Any

ABO_RULES: dict[str, tuple[str, ...]] = {
    "O": ("O",),
    "A": ("A", "O"),
    "B": ("B", "O"),
    "AB": ("A", "B", "AB", "O"),
}
RH_RULES: dict[str, tuple[str, ...]] = {
    "negative": ("negative",),
    "positive": ("positive", "negative"),
}
VALID_COMPONENTS = frozenset({"whole_blood", "packed_rbc", "washed_rbc", "irradiated_rbc", "leukocyte_reduced", "ffp", "platelet_concentrate", "cryoprecipitate", "cryosupernatant", "granulocytes"})
POLICY_VERSION = "abo-rh-component-v1"


def _parse_group(value: str | None) -> tuple[str | None, str | None]:
    if not value or not value.strip():
        return None, None
    raw = value.strip()
    abo = raw.replace("+", "").replace("-", "").upper()
    if abo not in ABO_RULES or not raw[-1:] in {"+", "-"}:
        return None, None
    return abo, "positive" if raw[-1] == "+" else "negative"


def check_compatibility(patient_group: str, unit_group: str, *, component: str = "packed_rbc") -> dict[str, Any]:
    patient_abo, patient_rh = _parse_group(patient_group)
    unit_abo, unit_rh = _parse_group(unit_group)
    valid = bool(patient_abo and patient_rh and unit_abo and unit_rh and component in VALID_COMPONENTS)
    abo_ok = bool(valid and unit_abo in ABO_RULES[patient_abo])
    rh_ok = bool(valid and unit_rh in RH_RULES[patient_rh])
    compatible = abo_ok and rh_ok
    if not valid:
        result = "Indeterminate: valid ABO/Rh group and component are required"
    elif compatible:
        result = f"Compatible under policy {POLICY_VERSION}: {unit_group} → {patient_group}"
    else:
        result = "; ".join(("ABO incompatible", "Rh incompatible") if not abo_ok and not rh_ok else (("ABO incompatible",) if not abo_ok else ("Rh incompatible",)))
    return {"compatible": compatible, "indeterminate": not valid, "abo_compatible": abo_ok, "rh_compatible": rh_ok, "patient_group": patient_group, "unit_group": unit_group, "component": component, "policy_version": POLICY_VERSION, "result": result}


def get_compatible_groups(patient_group: str, *, component: str = "packed_rbc") -> list[dict[str, Any]]:
    patient_abo, patient_rh = _parse_group(patient_group)
    if not patient_abo or not patient_rh or component not in VALID_COMPONENTS:
        return []
    result = []
    for abo in ABO_RULES[patient_abo]:
        for rh in RH_RULES[patient_rh]:
            result.append({"group": f"{abo}{'+' if rh == 'positive' else '-'}", "abo_compatible": True, "rh_compatible": True, "policy_version": POLICY_VERSION})
    return result
