"""The secret-scanning gate was failing on a permission, not on a secret.

IA-090. `Secret Scan` in `.github/workflows/security-hardening.yml` has two
steps. The first, `scripts/security/check_public_secrets.py`, was passing:

    OK: no likely public secrets found in tracked source files

The second, `gitleaks/gitleaks-action`, crashed before scanning. On a
`pull_request` event it scopes the scan by calling

    GET /repos/samertts/gula-platform/pulls/261/commits

and the job's token held only `contents: read` and `security-events: write`, so
GitHub answered 403 `Resource not accessible by integration` and named the
missing grant in its own response header:

    x-accepted-github-permissions: pull_requests=read

The action then exited non-zero with an unhandled `RequestError [HttpError]`.
The check read `failure`, which looks like a finding and was an outage: no
history scan has run on a pull request in this repository.

That is why these assertions exist rather than a note in a report. A red gate
that is red for a non-finding trains everyone to ignore it, and the next time
it goes red for a real leaked credential it will look the same.

WHY THERE IS NO `yaml` IMPORT HERE. The first version of this file opened with
`pytest.importorskip("yaml")`. PyYAML is declared in neither
`backend/requirements.txt` nor `backend/requirements-dev.txt`, so in the
`Backend Tests` job that line would have skipped every assertion below — a
ratchet that guards nothing, installed to guard something. The block is read
by indentation instead, which needs no dependency and cannot skip. The reader
is deliberately narrow and asserts that it found what it was looking for, so a
restructured workflow fails here rather than passing on an empty parse.

Scope note: this file asserts the workflow's declared permissions, which is
what the failure was. It cannot assert that gitleaks finds anything — that
needs a token and a runner.
"""
from __future__ import annotations

import pathlib

REPO = pathlib.Path(__file__).resolve().parents[3]
WORKFLOW = REPO / ".github" / "workflows" / "security-hardening.yml"

#: The step that needs the grant, pinned by the action it runs rather than by
#: its display name, so renaming the step does not quietly void this.
GITLEAKS_ACTION = "gitleaks/gitleaks-action"

JOB = "secret-scan"


def _lines() -> list[str]:
    return WORKFLOW.read_text(encoding="utf-8").splitlines()


def _block(lines: list[str], header: str, indent: int) -> list[str]:
    """The lines indented under ``header`` at ``indent`` columns.

    Comment and blank lines inside the block are kept, because a comment there
    is part of what a reader sees; callers ignore them.
    """
    wanted = f"{' ' * indent}{header}"
    try:
        start = next(i for i, line in enumerate(lines) if line.rstrip() == wanted)
    except StopIteration:
        return []
    body: list[str] = []
    for line in lines[start + 1:]:
        if not line.strip():
            body.append(line)
            continue
        if len(line) - len(line.lstrip()) <= indent:
            break
        body.append(line)
    return body


def _mapping(block: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in block:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or ":" not in stripped:
            continue
        key, _, value = stripped.partition(":")
        out[key.strip()] = value.strip()
    return out


def _job_block() -> list[str]:
    return _block(_lines(), f"{JOB}:", indent=2)


def _permissions() -> dict[str, str]:
    return _mapping(_block(_job_block(), "permissions:", indent=4))


def test_the_reader_found_the_job_and_its_permissions():
    """Positive control for every assertion below.

    Without this, a renamed job or a restructured file would make the reader
    return an empty block and the permission assertions would be comparing
    `None` to `None`-ish nothing.
    """
    assert WORKFLOW.exists(), WORKFLOW
    job = _job_block()
    assert job, f"no `{JOB}:` job block found in {WORKFLOW.name}"
    assert any("runs-on" in line for line in job), (
        "the block read does not look like a job; the reader or the workflow "
        "layout has changed"
    )
    permissions = _permissions()
    assert permissions, f"no `permissions:` block under `{JOB}:`"
    # Structure only. Which grants are required is asserted by the tests that
    # name them, so this control stays true while those ratchet.
    assert len(permissions) >= 2, permissions
    assert all(value in {"read", "write", "none"} for value in permissions.values()), (
        f"the reader did not produce a permissions mapping: {permissions}"
    )


def test_the_secret_scan_job_still_runs_gitleaks():
    """Positive control: the grant below is only needed while this step is here."""
    job = "\n".join(_job_block())
    assert GITLEAKS_ACTION in job, (
        f"no {GITLEAKS_ACTION} step found in the {JOB} job"
    )


def test_the_secret_scan_job_can_read_pull_requests():
    """The assertion that would have caught IA-090."""
    permissions = _permissions()
    assert permissions.get("pull-requests") == "read", (
        f"the {JOB} job cannot list a pull request's commits without "
        f"`pull-requests: read`, so gitleaks-action exits 403 before scanning "
        f"and the gate reports a permission error as if it were a finding "
        f"(IA-090). GitHub itself names the grant: "
        f"x-accepted-github-permissions: pull_requests=read. "
        f"Declared now: {permissions}"
    )


def test_the_job_keeps_the_grants_it_already_needed():
    """Ratchet the other direction too: the fix must not displace anything."""
    permissions = _permissions()
    assert permissions.get("contents") == "read", permissions
    assert permissions.get("security-events") == "write", permissions


def test_the_grant_stays_read_only():
    """`pull-requests: write` would let a scanner comment and label.

    It does not need to, and a secret scanner is the last job to widen.
    """
    permissions = _permissions()
    assert permissions.get("pull-requests") != "write", (
        "the scan only lists commits; read is sufficient and write is not"
    )


def test_the_repository_source_guard_step_is_still_there():
    """The step that was already passing must not be dropped on the way past."""
    job = "\n".join(_job_block())
    assert "check_public_secrets.py" in job, (
        "the repository source guard is the half of this gate that works; "
        "it stays."
    )
    guard = REPO / "scripts" / "security" / "check_public_secrets.py"
    assert guard.exists(), guard
