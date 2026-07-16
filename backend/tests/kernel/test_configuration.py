from __future__ import annotations

import pytest

from app.kernel.config.registry import ConfigurationRegistry
from app.kernel.config.validation import ConfigurationValidator


class TestConfigurationRegistry:
    def test_set_and_get(self):
        cr = ConfigurationRegistry()
        cr.set("db.host", "localhost")
        assert cr.get("db.host") == "localhost"
        assert cr.get("nonexistent", "default") == "default"
        assert cr.has("db.host")
        assert not cr.has("nonexistent")

    def test_get_required(self):
        cr = ConfigurationRegistry()
        cr.set("key", "value")
        assert cr.get_required("key") == "value"
        with pytest.raises(KeyError):
            cr.get_required("nonexistent")

    def test_all(self):
        cr = ConfigurationRegistry()
        cr.set("a", 1)
        cr.set("b", 2)
        assert cr.all() == {"a": 1, "b": 2}


class TestConfigurationValidator:
    def test_validate(self):
        cv = ConfigurationValidator()
        cv.register_schema("port", {"type": "int"})
        cv.validate("port", 8080)
        with pytest.raises(TypeError):
            cv.validate("port", "string")
