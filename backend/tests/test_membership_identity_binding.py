"""NR-141 — a membership carries the applicant's own identity, never a chosen one.

MembershipApplicationRequest carried `identity_id`, and the route passed
`body.identity_id or actor.account.identity_id` to create_application, which
never validated it. On approval the Membership was built with
`identity_id=application.identity_id`, so an applicant could end up holding a
membership -- the record that carries organizational scope -- bound to an
identity that is not theirs.

The sibling path was already correct: accept_invitation builds its Membership
with `identity_id=account.identity_id`. The same column was populated from the
server on one path and from the client on the other.
"""
from __future__ import annotations

import ast
import inspect
from pathlib import Path

from app.identity.api import memberships as memberships_module


def test_the_application_request_cannot_name_an_identity():
    """Removed rather than ignored, so no client believes it still chooses."""
    fields = memberships_module.MembershipApplicationRequest.model_fields
    assert "identity_id" not in fields, (
        "a client must not be able to name the identity its membership binds to; "
        f"declared fields: {sorted(fields)}"
    )


def test_the_route_derives_the_identity_from_the_authenticated_account():
    source = inspect.getsource(memberships_module.submit_membership_application)
    assert "identity_id=actor.account.identity_id" in source
    assert "body.identity_id" not in source, (
        "the body must not reach identity_id by any route"
    )


def test_the_positive_control_the_route_still_reads_the_body_for_context():
    """Without this, the assertions above would also pass on a route that
    ignored the request entirely, which would be a different bug."""
    source = inspect.getsource(memberships_module.submit_membership_application)
    for field in ("organization_id", "relationship_type", "scope_type"):
        assert f"body.{field}" in source, f"{field} should still come from the request"


def test_no_request_model_in_this_module_accepts_an_identity_or_account_id():
    """The defect class, not just the one instance.

    A request model that accepts identity_id, account_id or person_id is a
    client naming whose identity a record binds to. recipient_account_id is
    excluded deliberately: an invitation names its recipient by design, and
    accept_invitation still derives the Membership's identity from the
    authenticated account rather than from the invitation.
    """
    source = Path(inspect.getfile(memberships_module)).read_text(encoding="utf-8")
    tree = ast.parse(source)
    allowed = {"recipient_account_id"}
    offenders = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef) or not node.name.endswith("Request"):
            continue
        for stmt in node.body:
            if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                name = stmt.target.id
                if name in {"identity_id", "account_id", "person_id"} and name not in allowed:
                    offenders.append(f"{node.name}.{name}")
    assert offenders == [], (
        f"these request models let a client name an identity: {offenders}"
    )


def test_the_scan_actually_sees_the_request_models():
    """Positive control: an empty sweep would pass vacuously."""
    source = Path(inspect.getfile(memberships_module)).read_text(encoding="utf-8")
    tree = ast.parse(source)
    models = [n.name for n in ast.walk(tree)
              if isinstance(n, ast.ClassDef) and n.name.endswith("Request")]
    assert len(models) >= 3, f"only found {models}"
