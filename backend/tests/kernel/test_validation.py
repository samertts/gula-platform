from __future__ import annotations

import asyncio

import pytest

from backend.app.kernel import Kernel
from backend.app.kernel.validation.architecture import ArchitectureValidator
from backend.app.kernel.validation.dependencies import DependencyValidator
from backend.app.kernel.validation.memory import MemoryValidator
from backend.app.kernel.validation.performance import PerformanceValidator
from backend.app.kernel.validation.security import SecurityValidator
from backend.app.kernel.validation.stress import StressTester


class TestArchitectureValidator:
    def test_validate_returns_issues(self, kernel: Kernel):
        validator = ArchitectureValidator(kernel)
        issues = validator.validate()
        assert len(issues) > 0

    def test_missing_components(self, kernel: Kernel):
        validator = ArchitectureValidator(kernel)
        issues = validator.validate()
        missing = [i for i in issues if i["type"] == "missing_component"]
        assert len(missing) > 0


class TestDependencyValidator:
    def test_validate(self, kernel: Kernel):
        validator = DependencyValidator(kernel)
        issues = validator.validate()
        assert isinstance(issues, list)

    def test_empty(self, kernel: Kernel):
        validator = DependencyValidator(kernel)
        issues = validator.validate()
        assert len(issues) == 0


class TestSecurityValidator:
    def test_validate(self, kernel: Kernel):
        validator = SecurityValidator(kernel)
        issues = validator.validate()
        assert isinstance(issues, list)

    def test_empty(self, kernel: Kernel):
        validator = SecurityValidator(kernel)
        issues = validator.validate()
        assert len(issues) == 0


class TestPerformanceValidator:
    def test_validate(self, kernel: Kernel):
        validator = PerformanceValidator(kernel)
        issues = validator.validate()
        assert isinstance(issues, list)


class TestMemoryValidator:
    def test_validate(self, kernel: Kernel):
        validator = MemoryValidator(kernel)
        issues = validator.validate()
        assert isinstance(issues, list)


class TestStressTester:
    def test_run(self, kernel: Kernel):
        tester = StressTester(kernel)
        result = asyncio.run(tester.run(iterations=10))
        assert result["iterations"] == 10
        assert result["total_time_ms"] >= 0

    def test_result_details(self, kernel: Kernel):
        tester = StressTester(kernel)
        result = asyncio.run(tester.run(iterations=5))
        assert result["iterations"] == 5
        assert result["total_time_ms"] >= 0
        assert result["avg_time_ms"] >= 0
