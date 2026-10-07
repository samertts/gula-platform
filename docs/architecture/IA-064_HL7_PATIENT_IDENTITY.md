# IA-064 — two patients' lab results collapsed onto one FHIR identity

**Severity** P0 · **Confidence** CONFIRMED · **Reachability** reachable, `POST /fhir-interoperability/hl7/convert`
**Fix status** FIXED — `f124230f` on `claude/independent-audit-1`
**Negative proofs** NP-AM, NP-AN, NP-AO, NP-AP, NP-AQ — all restored byte-identically (sha256)

---

## The defect

`app/capabilities/fhir_interoperability/hl7.py::to_fhir_bundle` derived every
identity in the bundle from two HL7 fields, and substituted a literal whenever
either was absent:

```python
patient_id     = message.patient_identifier or "synthetic-patient"
report_id      = f"report-{message.control_id or 'synthetic'}"
observation_id = f"obs-{message.control_id or 'synthetic'}-{index}"
```

Measured before the repair, with two different patients and two clinically
opposite results:

| | `Patient` id | `Observation` id | `DiagnosticReport` id | value |
|---|---|---|---|---|
| ALI AHMED | `synthetic-patient` | `obs-synthetic-1` | `report-synthetic` | glucose **3.1** mmol/L |
| FATIMA HASSAN | `synthetic-patient` | `obs-synthetic-1` | `report-synthetic` | glucose **19.4** mmol/L |

All three identities are **identical**.

> In any FHIR store that upserts by resource id, the second message silently
> overwrites the first, or the two merge into one patient record carrying a
> hypoglycaemia and a severe hyperglycaemia at once. A result attributed to the
> wrong patient is the worst class of laboratory error — it is the one that
> leads directly to treating the wrong person.

Nothing about this was marked, warned, or logged. The endpoint returned 200
with a `"simulationOnly": true` flag, which describes the data's provenance,
not the identity collision.

## Same family as IA-061

IA-061 was `result_to_fhir` publishing `Patient/unknown` from a `hasattr`
fallback. Same shape, same consequence, same repair: **refuse rather than
guess**.

## The repair

**PID-3, MSH-10, OBR-4 and OBX-3 are all Required (R) in an ORU^R01 under HL7
v2.5.** So refusing a message that omits one is faithful to the standard, not
merely the cautious choice — the alternative was accepting malformed input and
inventing the missing part.

Two layers:

1. **`parse_oru_r01`** refuses at the boundary, in the same idiom the file
   already used for `"must contain at least one OBX segment"`. The route maps
   `HL7ConversionError` to 422, so this reaches the client as malformed input.
2. **`to_fhir_bundle`** refuses as well. `HL7Message` is a public frozen
   dataclass that callers construct without the parser, so a guard only at the
   parse boundary would be bypassable — and is, by this suite's own tests.

`to_fhir_bundle` was also called **outside** the `try` that catches
`HL7ConversionError`, so its guards would have surfaced as a 500. It is inside
now.

## Two further sites found by the ratchet, not by reading

I wrote `FORBIDDEN_PLACEHOLDERS = ("synthetic-patient", "synthetic",
"unknown", "anonymous")` as a generalisation beyond the two literals I had
found. It immediately failed on a site I had not looked at:

```python
code = item.get("code") or "unknown"                # OBX-3
message.service_code or "laboratory-panel"          # OBR-4
```

The first published a numeric result as a measurement of `"unknown"` — **a lab
value with no analyte**, which cannot be interpreted and cannot be safely
stored. The second asserted a panel identity (`laboratory-panel`) that the
sending facility never stated. Both are inventing clinical semantics, which
the standing brief forbids outright. Both now refuse.

This is what a generalised ratchet is for: the two literals I knew about would
have been pinned by an exact-match test, and the other two would have
survived.

## Negative proofs

| ID | Perturbation | Named tests that failed | Restored |
|----|-------------|-------------------------|----------|
| NP-AM | restore the patient-id substitution | 2 (both AST ratchets) | sha256 OK |
| NP-AN | restore the report-id substitution | 2 (both AST ratchets) | sha256 OK |
| NP-AO | restore `or "unknown"` on OBX-3 | `test_the_placeholder_literals_are_gone_from_executable_code` | sha256 OK |
| NP-AP | restore `or "laboratory-panel"` on OBR-4 | `test_no_identity_field_is_defaulted_with_or` | sha256 OK |
| NP-AQ | **remove the explicit refusal AND restore the substitution as a conditional expression, to evade the AST ratchet** | `test_the_bundle_builder_refuses_too[patient_identifier]` — a **behavioural** test | sha256 OK |

### Why NP-AQ was necessary

NP-AM and NP-AN failed only the two AST ratchets, not any behavioural test.
The reason is benign — `parse_oru_r01` refuses first, so the substitution
downstream is unreachable — but NP-AH on IA-074 taught that **a source-position
assertion is not a behavioural assertion**, and two source assertions are not
two independent proofs.

So NP-AQ removed the explicit `raise` *and* rewrote the substitution as
`x if x else "synthetic-patient"`, which the `BoolOp`-based AST ratchet does
not match. A behavioural test caught it. The guards are layered, not
decorative.

## An earlier test asserted the defect

`tests/verification/test_fhir_patient_identity.py` already contained:

```python
def test_ia064_two_messages_with_no_patient_identifier_collapse_into_one_patient(...):
    assert refs[0] == refs[1] == "Patient/synthetic-patient", refs
```

That was this audit's own **record of the then-unfixed defect**, not a guard on
correct behaviour, so the repair made it fail. It is rewritten to assert the
refusal, with the original assertion quoted in its docstring so the history is
preserved rather than erased.

Its two sibling IA-064 tests pass unchanged: the one that checks PID-3 is used
as the FHIR id when it *is* present, and the one that records that the
`synthetic-only` tag sits on the bundle rather than on each resource.

## Suite state

`tests/verification/` + `tests/notifications/` + `tests/test_fhir_interoperability.py`
— **978 passed**, 151 skipped, 2 xfailed, **0 failed**. `py_compile` and
`pyflakes` clean.

## What this does and does not establish

It establishes that the served HL7→FHIR converter can no longer attribute a
result to a guessed patient, a guessed report, or a guessed analyte, and that
a malformed message is reported as such instead of being silently completed.

It does **not** establish anything about the other FHIR paths beyond what
`test_fhir_patient_identity.py` already recorded, nor that any inbound HL7
feed exists in production — the module's docstring calls itself a converter
for "synthetic gateway messages", and whether a real instrument feed is wired
to this endpoint was **not measured**. The repair is correct either way: a
converter that invents identities is wrong whether or not it is currently fed
real data, and the three-reference-shape inconsistency recorded as IA-063
remains open and untouched.
