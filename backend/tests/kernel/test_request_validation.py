from __future__ import annotations

import pytest

from app.kernel.gateway.validation import RequestValidator


class TestRequestValidator:
    def test_register_and_validate(self):
        rv = RequestValidator()

        def must_be_dict(req):
            return isinstance(req, dict)

        rv.register("/api/data", must_be_dict)
        assert rv.validate("/api/data", {"ok": True})
        assert not rv.validate("/api/data", "string")

    def test_no_validator(self):
        rv = RequestValidator()
        assert rv.validate("/unregistered", "anything")
