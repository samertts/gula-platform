from typing import Any


class AuthService:
    def __init__(self, monolith_adapter=None):
        self._monolith = monolith_adapter

    async def get_current_user(self, token: str) -> dict[str, Any] | None:
        if self._monolith is None:
            return None
        try:
            get_user = self._monolith.get_current_user_dependency()
            if get_user is None:
                return None
            return {"authenticated": True, "token": token}
        except Exception:
            return None

    async def validate_lab_access(self, user: dict[str, Any] | None, lab_id: str) -> bool:
        if user is None:
            return False
        return True
