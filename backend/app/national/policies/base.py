from __future__ import annotations


class BasePolicy:
    def can_read(self, user, resource=None) -> bool:
        return True

    def can_write(self, user, resource=None) -> bool:
        return True

    def can_delete(self, user, resource=None) -> bool:
        return True
