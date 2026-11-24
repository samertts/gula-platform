"""Add account_kind to oauth2_tokens (AUD-API-002 / AUD-SEC-002).

OAuth2 access tokens were minted with type="oauth2_access", which the canonical
decode_token()/get_current_user() chain rejects, so every OAuth2 token was
unusable against GULA's own API. Unifying the token type requires resolving the
subject's account domain, but the persisted ``user_id`` is ambiguous because
LabUser.id and User.id are independent primary-key spaces. This nullable column
records the domain at authorization time.

Backwards compatible: the column is nullable and there is no data migration.
Legacy OAuth2 token records (NULL account_kind) remain usable for
introspection/revocation only. They **cannot** mint a canonical, subject-bearing
access token until re-authorized: claim resolution returns no identity claims
for a NULL/unknown domain, and the provider refuses to embed a ``user_id`` in a
token that carries no signed, resolvable account domain. This is deliberate
fail-closed behavior — without it, a bare ``user_id`` would be *guessed* to
belong to the User family by ``resolve_token_account_kind()`` (its legacy
lab_id-derived fallback), which could bind a legacy LabUser subject to a
colliding User account and reintroduce AUD-SEC-002 through the OAuth2 path.
Their pre-fix tokens were unusable against GULA's API in any case.
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20261118_0001"
down_revision = "20261114_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("oauth2_tokens", sa.Column("account_kind", sa.String(length=20), nullable=True))


def downgrade() -> None:
    op.drop_column("oauth2_tokens", "account_kind")
