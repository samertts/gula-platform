from __future__ import annotations

ABO_RULES: dict[str, list[str]] = {
    "O": ["O"],
    "A": ["A", "O"],
    "B": ["B", "O"],
    "AB": ["A", "B", "AB", "O"],
}

RH_RULES: dict[str, list[str]] = {
    "negative": ["negative", "positive"],
    "positive": ["positive"],
}


def check_compatibility(patient_group: str, unit_group: str) -> dict:
    patient_abo = patient_group.replace("+", "").replace("-", "").upper() if patient_group else "O"
    patient_rh = "positive" if "+" in patient_group else "negative"
    unit_abo = unit_group.replace("+", "").replace("-", "").upper() if unit_group else "O"
    unit_rh = "positive" if "+" in unit_group else "negative"

    abo_ok = unit_abo in ABO_RULES.get(patient_abo, [])
    rh_ok = unit_rh in RH_RULES.get(patient_rh, [])

    compatible = abo_ok and rh_ok
    result_parts = []
    if not abo_ok:
        result_parts.append(f"ABO incompatible: patient {patient_abo} cannot receive {unit_abo}")
    if not rh_ok:
        result_parts.append(f"Rh incompatible: patient {patient_rh} cannot receive {unit_rh}")
    if compatible:
        result_parts.append(f"Compatible: {unit_group} → {patient_group}")

    return {
        "compatible": compatible,
        "abo_compatible": abo_ok,
        "rh_compatible": rh_ok,
        "patient_group": patient_group,
        "unit_group": unit_group,
        "result": "; ".join(result_parts),
    }


def get_compatible_groups(patient_group: str) -> list[dict]:
    abo = patient_group.replace("+", "").replace("-", "").upper() if patient_group else "O"
    rh = "positive" if "+" in patient_group else "negative"
    compatible_abo = ABO_RULES.get(abo, [])
    compatible_rh = RH_RULES.get(rh, [])
    result = []
    for ca in compatible_abo:
        for cr in compatible_rh:
            group = f"{ca}+" if cr == "positive" else f"{ca}-"
            result.append({"group": group, "abo_compatible": True, "rh_compatible": ca == abo})
    return result
