"""NR-035: a token must say which identity table it means.

`users` and `lab_users` are two identity tables with independent integer
primary keys. Until AUTH-003 the access token carried only `user_id`, and
`get_current_user` resolved it by querying `LabUser` first and falling back to
`User`. A token issued for `users.id = N` therefore resolved to
`lab_users.id = N` whenever that row existed — silently, with that laboratory
user's role and tenant.

It was latent rather than live only because `users` holds no rows in the
deployed schema. It becomes exploitable the moment citizens are registered,
which is precisely what the citizen-entry work would do.

The fix is the discriminator the platform already models everywhere else:
`get_perm_version` takes `account_kind="user"|"lab"`, and
`LegacyAccountLinkSource` is exactly `{user, lab_user}`. It is now carried in
the token as `act`, and resolution selects exactly one table.

Tokens minted before the change have no `act`. Rather than invalidate every
live session, those still resolve by search — but fail closed when the id
exists in both tables, which is the only case the old behaviour could get
wrong. Ambiguity is refused, never guessed.
"""

from __future__ import annotations

import pytest
from app.models.lab import Lab
from app.models.lab_user import LabUser
from app.models.user import User
from app.security.auth import (
    ACCOUNT_KIND_LAB,
    ACCOUNT_KIND_USER,
    build_token_payload,
    create_token,
    decode_token,
)
from app.security.dependencies import resolve_token_subject


@pytest.fixture()
def colliding_identities(db):
    """One `users` row and one `lab_users` row sharing an integer id.

    This is the state the platform is one citizen-registration away from, and
    the state the old resolver could not distinguish.
    """
    lab = Lab(name="NR-035 Lab", lab_type="clinical")
    db.add(lab)
    db.flush()

    shared_id = 770035
    lab_user = LabUser(
        id=shared_id, lab_id=lab.id, name="Laboratory User",
        email="labuser-nr035@example.invalid", password_hash="!x",
        role="lab_admin", is_active=True, perm_version=1,
    )
    citizen = User(
        id=shared_id, full_name="Citizen Person", email="citizen-nr035@example.invalid",
        phone="07700350000", password_hash="!x", role="citizen",
        is_active=True, is_verified=True,
    )
    db.add_all([lab_user, citizen])
    db.flush()
    return shared_id, lab_user, citizen


# ── the discriminator is issued ──────────────────────────────────────────────


def test_a_staff_token_declares_the_laboratory_identity_table() -> None:
    class Staff:
        id, lab_id, role, perm_version = 5, 3, "doctor", 1

    claims = decode_token(create_token(build_token_payload(Staff(), ACCOUNT_KIND_LAB)))
    assert claims["act"] == ACCOUNT_KIND_LAB
    assert claims["user_id"] == 5


def test_an_unknown_account_kind_is_refused_at_mint_time() -> None:
    class Staff:
        id, lab_id, role, perm_version = 5, 3, "doctor", 1

    with pytest.raises(ValueError, match="Unknown account kind"):
        build_token_payload(Staff(), "ministry")


# ── resolution selects exactly one table ─────────────────────────────────────


def test_a_lab_token_resolves_to_the_lab_user_even_when_ids_collide(
    db, colliding_identities,
) -> None:
    shared_id, lab_user, _citizen = colliding_identities
    resolved = resolve_token_subject(db, {"user_id": shared_id, "act": ACCOUNT_KIND_LAB})
    assert isinstance(resolved, LabUser)
    assert resolved.id == lab_user.id
    assert resolved.lab_id == lab_user.lab_id


def test_a_citizen_token_resolves_to_the_citizen_even_when_ids_collide(
    db, colliding_identities,
) -> None:
    """The half that was dangerous: this used to return the laboratory user."""
    shared_id, _lab_user, citizen = colliding_identities
    resolved = resolve_token_subject(db, {"user_id": shared_id, "act": ACCOUNT_KIND_USER})
    assert isinstance(resolved, User)
    assert resolved.id == citizen.id
    assert resolved.role == "citizen"
    assert getattr(resolved, "lab_id", None) is None, (
        "a citizen must not acquire a laboratory tenant by id collision"
    )


def test_an_unknown_discriminator_fails_closed(db, colliding_identities) -> None:
    shared_id, _lab, _citizen = colliding_identities
    assert resolve_token_subject(db, {"user_id": shared_id, "act": "ministry"}) is None


def test_a_missing_subject_fails_closed(db) -> None:
    assert resolve_token_subject(db, {"act": ACCOUNT_KIND_LAB}) is None


# ── legacy tokens: compatible, but never ambiguous ───────────────────────────


def test_a_legacy_token_without_a_discriminator_still_resolves_when_unambiguous(db) -> None:
    """Live sessions must not be invalidated by this change."""
    lab = Lab(name="NR-035 Legacy Lab", lab_type="clinical")
    db.add(lab)
    db.flush()
    lab_user = LabUser(
        id=770036, lab_id=lab.id, name="Only Laboratory User",
        email="only-nr035@example.invalid", password_hash="!x",
        role="doctor", is_active=True, perm_version=1,
    )
    db.add(lab_user)
    db.flush()

    resolved = resolve_token_subject(db, {"user_id": 770036})
    assert isinstance(resolved, LabUser)
    assert resolved.id == 770036


def test_a_legacy_token_refuses_rather_than_guesses_when_the_id_is_ambiguous(
    db, colliding_identities,
) -> None:
    """The defect itself.

    Before AUTH-003 this returned the laboratory user, handing a citizen's
    token that user's role and tenant. It must now refuse.
    """
    shared_id, _lab_user, _citizen = colliding_identities
    assert resolve_token_subject(db, {"user_id": shared_id}) is None, (
        "an ambiguous legacy token resolved to an identity instead of failing closed"
    )


def test_the_old_behaviour_would_have_returned_the_wrong_identity(
    db, colliding_identities,
) -> None:
    """Pin what the defect actually was, so the fix cannot be undone quietly.

    This reproduces the previous resolution order directly. It is not a call
    into production code — it is the shape the code used to have, kept here as
    the record of why the discriminator exists.
    """
    shared_id, lab_user, citizen = colliding_identities

    old_result = db.query(LabUser).filter(LabUser.id == shared_id, LabUser.is_active).first()
    if old_result is None:
        old_result = (
            db.query(User)
            .filter(User.id == shared_id, User.is_active, User.is_verified)
            .first()
        )

    assert isinstance(old_result, LabUser), "the old order preferred lab_users"
    assert old_result.id == citizen.id, "same integer, different person"
    assert old_result.lab_id == lab_user.lab_id, (
        "a citizen's token would have carried this laboratory tenant"
    )
    # And what the platform does now with the same input:
    assert resolve_token_subject(db, {"user_id": shared_id}) is None


# ── the fix has to hold everywhere a token is minted or resolved ─────────────


def _app_modules() -> list:
    import pathlib

    app_root = pathlib.Path(__file__).resolve().parents[1] / "app"
    return [p for p in app_root.rglob("*.py") if "__pycache__" not in p.parts]


def test_every_token_mint_site_declares_an_identity_table() -> None:
    """A token without `act` is an ambiguous token.

    Four places mint one: `build_token_payload` (staff), the citizen branch of
    `/login`, `/citizen/login`, and the mobile refresh rotation. Each builds a
    claims dict containing `perm_ver`. If a fifth appears without the
    discriminator, the ambiguity NR-035 closed is reopened for that path.
    """
    import re

    offenders = []
    for path in _app_modules():
        source = path.read_text(encoding="utf-8", errors="ignore")
        for match in re.finditer(r'"perm_ver"\s*:', source):
            # Read the enclosing dict literal: from the nearest preceding "{"
            # to the matching close. A mint site always sets "user_id" too;
            # a read site (payload.get("perm_ver", 1)) never does.
            start = source.rfind("{", 0, match.start())
            end = source.find("}", match.end())
            if start == -1 or end == -1:
                continue
            literal = source[start : end + 1]
            if '"user_id"' not in literal:
                continue  # reading a claim, not building one
            if '"act"' not in literal:
                offenders.append(f"{path.name}:{source[:match.start()].count(chr(10)) + 1}")

    assert not offenders, (
        f"token payloads built without an `act` discriminator: {offenders}. "
        "Every mint site must say which identity table `user_id` refers to."
    )


def test_no_module_resolves_the_same_id_against_both_identity_tables() -> None:
    """The defect's shape, not just its two instances.

    NR-035 existed twice — in `get_current_user` and in the mobile refresh
    rotation — because the same fallback was written twice: look the id up in
    `lab_users`, and if that misses, look *the same integer* up in `users`.
    Taking one id to both tables is what makes it ambiguous, and it is now
    expressed in exactly one place, which fails closed when both rows exist.

    Detected by the name being compared: a module that filters both
    `LabUser.id == x` and `User.id == x` for the same `x` has re-implemented
    the shape. Looking up two *different* ids is ordinary and untouched —
    `admin.py` fetches a `doctor_id` and a `user_id`, `labs.py` an
    `employee_id`, each additionally scoped or role-constrained.
    """
    import re

    lab_by_id = re.compile(r"\bLabUser\.id\s*==\s*([A-Za-z_][A-Za-z0-9_.]*)")
    user_by_id = re.compile(r"(?<!Lab)\bUser\.id\s*==\s*([A-Za-z_][A-Za-z0-9_.]*)")
    resolver = "security/dependencies.py"

    offenders = {}
    for path in _app_modules():
        if str(path).endswith(resolver):
            continue
        source = path.read_text(encoding="utf-8", errors="ignore")
        shared = set(lab_by_id.findall(source)) & set(user_by_id.findall(source))
        if shared:
            offenders[path.name] = sorted(shared)

    assert not offenders, (
        f"{offenders} take one id to both identity tables. That is the NR-035 "
        "shape: use resolve_token_subject(), which carries the `act` "
        "discriminator and refuses an id that exists in both."
    )


# ── revocation must land on the identity the token names (AUTH-F7) ───────────


def test_logout_revokes_the_citizen_and_not_the_colliding_lab_user(
    db, colliding_identities,
) -> None:
    """Revocation is only as precise as identity resolution.

    `/logout` bumps `perm_version` so that every outstanding token for that
    account stops validating — the safety net for a wiped Redis. It resolved
    the subject with the same LabUser-first fallback, so a citizen's logout
    bumped the laboratory user's version instead: the citizen stayed signed in
    everywhere, and an unrelated laboratory user was signed out.

    This exercises the composition `/logout` performs — resolve, then bump —
    with the discriminator the token now carries.
    """
    from app.security.session import bump_perm_version

    shared_id, lab_user, citizen = colliding_identities
    lab_before = lab_user.perm_version or 1
    citizen_before = citizen.perm_version or 1

    subject = resolve_token_subject(db, {"user_id": shared_id, "act": ACCOUNT_KIND_USER})
    assert isinstance(subject, User)
    bump_perm_version(subject, db, reason="logout")
    db.flush()

    assert citizen.perm_version == citizen_before + 1, "the citizen was not revoked"
    assert (lab_user.perm_version or 1) == lab_before, (
        "logging a citizen out revoked a laboratory user's sessions"
    )


def test_the_revocation_cache_key_already_separated_what_the_token_did_not(
    db, colliding_identities,
) -> None:
    """Evidence that the discriminator was missing only from the token.

    `perm_ver_key` has always namespaced Redis by account kind, and
    `get_perm_version` has always taken `account_kind`. Two colliding ids
    therefore had two distinct authoritative versions all along — the token was
    the one place that could not say which of them it meant.
    """
    from app.security.session import perm_ver_key

    shared_id, _lab_user, _citizen = colliding_identities
    assert perm_ver_key(shared_id, "lab") != perm_ver_key(shared_id, "user")
