from __future__ import annotations

from types import SimpleNamespace

import pytest
from app.identity.repositories.account_repository import AccountRepository


class _Result:
    def scalar_one_or_none(self):
        return SimpleNamespace(id="account-1")


class _Session:
    def __init__(self):
        self.statement = None

    async def execute(self, statement):
        self.statement = statement
        return _Result()


@pytest.mark.asyncio
async def test_find_by_login_includes_email_username_and_phone_predicates():
    session = _Session()
    result = await AccountRepository(session).find_by_login("07700000000")

    assert result.id == "account-1"
    compiled = str(session.statement)
    assert "accounts.email" in compiled
    assert "accounts.username" in compiled
    assert "accounts.phone" in compiled
    assert "accounts.is_active" in compiled
