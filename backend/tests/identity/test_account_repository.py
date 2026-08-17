from __future__ import annotations

from types import SimpleNamespace
from typing import Any, cast

import pytest
from app.identity.repositories.account_repository import AccountRepository


class _Result:
    def scalar_one_or_none(self) -> SimpleNamespace:
        return SimpleNamespace(id="account-1")


class _Session:
    def __init__(self) -> None:
        self.statement = None

    async def execute(self, statement: Any) -> _Result:
        self.statement = statement
        return _Result()


@pytest.mark.asyncio
async def test_find_by_login_includes_email_username_and_phone_predicates() -> None:
    session = _Session()
    result = await AccountRepository(cast(Any, session)).find_by_login("07700000000")

    assert result.id == "account-1"
    compiled = str(session.statement)
    assert "accounts.email" in compiled
    assert "accounts.username" in compiled
    assert "accounts.phone" in compiled
    assert "accounts.is_active" in compiled
