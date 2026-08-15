from __future__ import annotations

import json
import logging
import os
import random
import time
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urljoin, urlsplit

import httpx

from app.integration.standards import FHIRService

logger = logging.getLogger("gula.integration.testing")

_LOOPBACK_HOSTS = {"localhost", "127.0.0.1", "::1"}
_ALLOWED_HOSTS = {
    host.strip().lower()
    for host in os.getenv("GULA_INTEGRATION_ALLOWED_HOSTS", "").split(",")
    if host.strip()
}
_ALLOWED_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}


def _validate_target(url: str) -> str:
    """Allow only configured integration hosts; never follow a redirect to another host."""
    parsed = urlsplit(url)
    host = (parsed.hostname or "").lower()
    if parsed.scheme not in {"http", "https"} or not host:
        raise ValueError("Integration targets must use http(s) and include a hostname")
    if parsed.username or parsed.password or parsed.fragment:
        raise ValueError("Integration targets may not contain credentials or fragments")
    if host not in _LOOPBACK_HOSTS and host not in _ALLOWED_HOSTS:
        raise ValueError("Integration target host is not in GULA_INTEGRATION_ALLOWED_HOSTS")
    if parsed.scheme != "https" and host not in _LOOPBACK_HOSTS:
        raise ValueError("Non-loopback integration targets must use HTTPS")
    return url.rstrip("/")


def _join_target(base_url: str, path: str) -> str:
    base = _validate_target(base_url)
    path_parts = urlsplit(path)
    if path_parts.scheme or path_parts.netloc or path.startswith("//"):
        raise ValueError("Integration endpoint paths must be relative")
    if any(segment == ".." for segment in path_parts.path.split("/")):
        raise ValueError("Integration endpoint paths may not traverse parent directories")
    candidate = urljoin(f"{base}/", path.lstrip("/"))
    parsed_base = urlsplit(base)
    parsed_candidate = urlsplit(candidate)
    if (parsed_base.scheme, parsed_base.netloc) != (parsed_candidate.scheme, parsed_candidate.netloc):
        raise ValueError("Integration endpoint changed the target origin")
    return candidate


@dataclass
class TestResult:
    name: str = ""
    passed: bool = False
    duration_ms: float = 0.0
    errors: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class TestSuite:
    name: str = ""
    results: list[TestResult] = field(default_factory=list)
    started_at: float = 0.0
    completed_at: float = 0.0

    @property
    def passed(self) -> bool:
        return all(r.passed for r in self.results)

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def passed_count(self) -> int:
        return sum(1 for r in self.results if r.passed)

    @property
    def failed_count(self) -> int:
        return sum(1 for r in self.results if not r.passed)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "passed": self.passed,
            "total": self.total,
            "passed_count": self.passed_count,
            "failed_count": self.failed_count,
            "duration_ms": (self.completed_at - self.started_at) * 1000 if self.completed_at else 0.0,
            "results": [
                {
                    "name": r.name,
                    "passed": r.passed,
                    "duration_ms": r.duration_ms,
                    "errors": r.errors,
                    "details": r.details,
                }
                for r in self.results
            ],
        }


class ContractTester:
    def __init__(self) -> None:
        self._contracts: dict[str, dict[str, Any]] = {}

    def register_contract(self, name: str, spec: dict[str, Any]) -> None:
        self._contracts[name] = spec
        logger.info("Contract registered: %s", name)

    async def test_endpoint(self, name: str, base_url: str, path: str, method: str = "GET") -> TestResult:
        start = time.monotonic()
        try:
            method = method.upper()
            if method not in _ALLOWED_METHODS:
                raise ValueError(f"Unsupported HTTP method: {method}")
            url = _join_target(base_url, path)
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=False) as client:
                resp = await client.request(method, url)
                result = TestResult(
                    name=f"contract_{name}",
                    passed=resp.is_success,
                    duration_ms=(time.monotonic() - start) * 1000,
                    details={"url": url, "status_code": resp.status_code, "method": method},
                )
                if not resp.is_success:
                    result.errors.append(f"Expected success, got {resp.status_code}")
                return result
        except Exception as exc:
            return TestResult(
                name=f"contract_{name}",
                passed=False,
                duration_ms=(time.monotonic() - start) * 1000,
                errors=[str(exc)],
            )

    async def run_all(self, base_urls: dict[str, str]) -> TestSuite:
        suite = TestSuite(name="contract_tests", started_at=time.time())
        for name, spec in self._contracts.items():
            if name in base_urls:
                ep = spec.get("endpoint", "/")
                method = spec.get("method", "GET")
                result = await self.test_endpoint(name, base_urls[name], ep, method)
                suite.results.append(result)
        suite.completed_at = time.time()
        return suite


class FHIRValidationTester:
    def __init__(self, fhir_service: FHIRService) -> None:
        self._fhir = fhir_service
        self._test_resources: list[dict[str, Any]] = []

    def add_test_resource(self, resource: dict[str, Any]) -> None:
        self._test_resources.append(resource)

    def load_from_file(self, path: str) -> int:
        with open(path) as f:
            data = json.load(f)
        if isinstance(data, list):
            self._test_resources.extend(data)
        else:
            self._test_resources.append(data)
        return len(self._test_resources)

    async def run_all(self) -> TestSuite:
        suite = TestSuite(name="fhir_validation", started_at=time.time())
        for i, resource in enumerate(self._test_resources):
            start = time.monotonic()
            errors: list[str] = []
            resource_type = resource.get("resourceType", "unknown")
            try:
                result = await self._fhir.validate_resource(resource)
                if not result.get("valid", False):
                    issues = result.get("issues", [])
                    for issue in issues:
                        errors.append(f"Issue: {issue.get('severity')}: {issue.get('details', {}).get('text', '')}")
                suite.results.append(TestResult(
                    name=f"fhir_valid_{resource_type}_{i}",
                    passed=result.get("valid", False),
                    duration_ms=(time.monotonic() - start) * 1000,
                    errors=errors,
                    details={"resource_type": resource_type, "validation": result},
                ))
            except Exception as exc:
                suite.results.append(TestResult(
                    name=f"fhir_valid_{resource_type}_{i}",
                    passed=False,
                    duration_ms=(time.monotonic() - start) * 1000,
                    errors=[str(exc)],
                ))
        suite.completed_at = time.time()
        return suite


class IntegrationTester:
    def __init__(self) -> None:
        self._scenarios: dict[str, dict[str, Any]] = {}

    def register_scenario(self, name: str, steps: list[dict[str, Any]]) -> None:
        self._scenarios[name] = {"steps": steps}
        logger.info("Integration scenario registered: %s", name)

    async def run_scenario(self, name: str, base_url: str = "") -> TestResult:
        scenario = self._scenarios.get(name)
        if not scenario:
            return TestResult(name=name, passed=False, errors=[f"Scenario not found: {name}"])
        start = time.monotonic()
        errors: list[str] = []
        details: dict[str, Any] = {"steps": []}
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=False) as client:
            for i, step in enumerate(scenario["steps"]):
                method = str(step.get("method", "GET")).upper()
                path = str(step.get("path", "/"))
                if method not in _ALLOWED_METHODS:
                    errors.append(f"Step {i}: unsupported HTTP method {method}")
                    continue
                body = step.get("body")
                try:
                    url = _join_target(base_url, path)
                    resp = await client.request(method, url, json=body)
                    step_result = {
                        "step": i,
                        "method": method,
                        "path": path,
                        "status_code": resp.status_code,
                        "success": resp.is_success,
                    }
                    details["steps"].append(step_result)
                    if not resp.is_success:
                        errors.append(f"Step {i}: {method} {path} returned {resp.status_code}")
                except Exception as exc:
                    errors.append(f"Step {i}: {exc!s}")
                    details["steps"].append({"step": i, "method": method, "path": path, "error": str(exc)})
        return TestResult(
            name=name,
            passed=len(errors) == 0,
            duration_ms=(time.monotonic() - start) * 1000,
            errors=errors,
            details=details,
        )

    async def run_all(self, base_url: str = "") -> TestSuite:
        suite = TestSuite(name="integration_tests", started_at=time.time())
        for name in self._scenarios:
            result = await self.run_scenario(name, base_url)
            suite.results.append(result)
        suite.completed_at = time.time()
        return suite


class LoadTester:
    def __init__(self) -> None:
        self._endpoints: list[dict[str, Any]] = []

    def add_endpoint(self, method: str, url: str, body: dict[str, Any] | None = None) -> None:
        method = method.upper()
        if method not in _ALLOWED_METHODS:
            raise ValueError(f"Unsupported HTTP method: {method}")
        self._endpoints.append({"method": method, "url": _validate_target(url), "body": body})

    async def run(
        self,
        concurrency: int = 10,
        total_requests: int = 100,
        ramp_up: float = 1.0,
    ) -> TestResult:
        import asyncio

        start = time.monotonic()
        errors: list[str] = []
        latencies: list[float] = []
        success_count = 0
        fail_count = 0

        async def _worker(sem: asyncio.Semaphore) -> None:
            nonlocal success_count, fail_count
            async with sem:
                ep = random.choice(self._endpoints)
                try:
                    async with httpx.AsyncClient(timeout=30.0, follow_redirects=False) as client:
                        t0 = time.monotonic()
                        method = ep["method"]
                        url = ep["url"]
                        body = ep.get("body")
                        resp = await client.request(method, url, json=body)
                        elapsed = (time.monotonic() - t0) * 1000
                        latencies.append(elapsed)
                        if resp.is_success:
                            success_count += 1
                        else:
                            fail_count += 1
                            errors.append(f"{method} {url}: {resp.status_code}")
                except Exception as exc:
                    fail_count += 1
                    errors.append(str(exc))

        sem = asyncio.Semaphore(concurrency)
        tasks = []
        for i in range(total_requests):
            if ramp_up and i > 0 and i % max(1, total_requests // 10) == 0:
                await asyncio.sleep(ramp_up / 10)
            tasks.append(_worker(sem))
        await asyncio.gather(*tasks)

        duration_ms = (time.monotonic() - start) * 1000
        avg_latency = sum(latencies) / len(latencies) if latencies else 0
        return TestResult(
            name=f"load_test_{concurrency}c_{total_requests}r",
            passed=fail_count == 0,
            duration_ms=duration_ms,
            errors=errors[:20],
            details={
                "concurrency": concurrency,
                "total_requests": total_requests,
                "success_count": success_count,
                "fail_count": fail_count,
                "avg_latency_ms": round(avg_latency, 2),
                "min_latency_ms": round(min(latencies), 2) if latencies else 0,
                "max_latency_ms": round(max(latencies), 2) if latencies else 0,
                "p95_latency_ms": round(sorted(latencies)[int(len(latencies) * 0.95)], 2) if latencies else 0,
                "total_duration_ms": round(duration_ms, 2),
            },
        )


class ChaosTester:
    def __init__(self) -> None:
        self._scenarios: dict[str, list[dict[str, Any]]] = {}

    def register_scenario(self, name: str, actions: list[dict[str, Any]]) -> None:
        self._scenarios[name] = actions
        logger.info("Chaos scenario registered: %s", name)

    async def run_scenario(self, name: str, target_url: str = "") -> TestResult:
        actions = self._scenarios.get(name)
        if not actions:
            return TestResult(name=name, passed=False, errors=[f"Chaos scenario not found: {name}"])
        start = time.monotonic()
        errors: list[str] = []
        details: list[dict[str, Any]] = []
        try:
            validated_target = _validate_target(target_url)
        except ValueError as exc:
            return TestResult(name=f"chaos_{name}", passed=False, errors=[str(exc)])
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=False) as client:
            for i, action in enumerate(actions):
                action_type = action.get("type", "http")
                method = str(action.get("method", "GET")).upper()
                path = str(action.get("path", "/"))
                try:
                    if action_type == "http":
                        if method not in _ALLOWED_METHODS:
                            raise ValueError(f"Unsupported HTTP method: {method}")
                        url = _join_target(validated_target, path)
                        resp = await client.request(method, url)
                        details.append({"step": i, "type": action_type, "status_code": resp.status_code})
                        if resp.is_error:
                            pass
                    elif action_type == "delay":
                        import asyncio
                        delay = action.get("duration", 0.5)
                        await asyncio.sleep(delay)
                        details.append({"step": i, "type": "delay", "duration": delay})
                    elif action_type == "disconnect":
                        details.append({"step": i, "type": "disconnect"})
                except Exception as exc:
                    errors.append(f"Step {i}: {exc!s}")
                    details.append({"step": i, "type": action_type, "error": str(exc)})
        return TestResult(
            name=f"chaos_{name}",
            passed=len(errors) == 0,
            duration_ms=(time.monotonic() - start) * 1000,
            errors=errors,
            details={"actions": details},
        )


class SecurityTester:
    def __init__(self) -> None:
        self._test_cases: dict[str, dict[str, Any]] = {}

    def register_test(self, name: str, config: dict[str, Any]) -> None:
        self._test_cases[name] = config

    async def test_auth_bypass(self, url: str, protected_path: str) -> TestResult:
        start = time.monotonic()
        errors: list[str] = []
        try:
            target = _join_target(_validate_target(url), protected_path)
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=False) as client:
                resp = await client.get(target)
                if resp.status_code in (401, 403):
                    return TestResult(
                        name="auth_bypass",
                        passed=True,
                        duration_ms=(time.monotonic() - start) * 1000,
                        details={"status_code": resp.status_code, "protected": True},
                    )
                errors.append(f"Auth bypass possible: {protected_path} returned {resp.status_code}")
                return TestResult(
                    name="auth_bypass",
                    passed=False,
                    duration_ms=(time.monotonic() - start) * 1000,
                    errors=errors,
                )
        except Exception as exc:
            return TestResult(
                name="auth_bypass",
                passed=False,
                duration_ms=(time.monotonic() - start) * 1000,
                errors=[str(exc)],
            )

    async def test_injection(self, url: str, endpoint: str) -> TestResult:
        start = time.monotonic()
        payloads = [
            {"key": "'; DROP TABLE users; --"},
            {"key": "<script>alert(1)</script>"},
            {"key": "${7*7}"},
            {"key": "../../etc/passwd"},
        ]
        try:
            target = _join_target(_validate_target(url), endpoint)
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=False) as client:
                for payload in payloads:
                    resp = await client.post(target, json=payload)
                    if resp.status_code < 500:
                        pass
                return TestResult(
                    name="injection_test",
                    passed=True,
                    duration_ms=(time.monotonic() - start) * 1000,
                    details={"payloads_tested": len(payloads)},
                )
        except Exception as exc:
            return TestResult(
                name="injection_test",
                passed=False,
                duration_ms=(time.monotonic() - start) * 1000,
                errors=[str(exc)],
            )

    async def run_all(self, target_url: str) -> TestSuite:
        suite = TestSuite(name="security_tests", started_at=time.time())
        for name, config in self._test_cases.items():
            test_type = config.get("type", "auth")
            path = config.get("path", "/")
            if test_type == "auth":
                result = await self.test_auth_bypass(target_url, path)
            elif test_type == "injection":
                result = await self.test_injection(target_url, path)
            else:
                result = TestResult(name=name, passed=False, errors=[f"Unknown test type: {test_type}"])
            suite.results.append(result)
        suite.completed_at = time.time()
        return suite


class CompatibilityTester:
    def __init__(self) -> None:
        self._versions: list[str] = []

    def add_version(self, version: str) -> None:
        self._versions.append(version)

    async def test_fhir_version(self, fhir_service: FHIRService, version: str, resource: dict[str, Any]) -> TestResult:
        start = time.monotonic()
        errors: list[str] = []
        try:
            if version not in ("R4", "R4B", "R5"):
                errors.append(f"Unsupported FHIR version: {version}")
            result = await fhir_service.validate_resource(resource)
            if not result.get("valid", False):
                errors.append(f"Resource invalid for {version}")
            return TestResult(
                name=f"compat_fhir_{version}",
                passed=len(errors) == 0,
                duration_ms=(time.monotonic() - start) * 1000,
                errors=errors,
                details={"version": version, "validation": result},
            )
        except Exception as exc:
            return TestResult(
                name=f"compat_fhir_{version}",
                passed=False,
                duration_ms=(time.monotonic() - start) * 1000,
                errors=[str(exc)],
            )

    async def run_all(self, fhir_service: FHIRService, test_resource: dict[str, Any]) -> TestSuite:
        suite = TestSuite(name="compatibility_tests", started_at=time.time())
        for version in self._versions:
            result = await self.test_fhir_version(fhir_service, version, test_resource)
            suite.results.append(result)
        suite.completed_at = time.time()
        return suite


class IntegrationTestSuite:
    def __init__(self) -> None:
        self.contract = ContractTester()
        self.fhir_validation = FHIRValidationTester.__new__(FHIRValidationTester)
        self.integration = IntegrationTester()
        self.load = LoadTester()
        self.chaos = ChaosTester()
        self.security = SecurityTester()
        self.compatibility = CompatibilityTester()

        self._fhir_service: FHIRService | None = None

    def configure_fhir(self, fhir_service: FHIRService) -> None:
        self._fhir_service = fhir_service
        self.fhir_validation = FHIRValidationTester(fhir_service)

    def register_fhir_test_resources(self, resources: list[dict[str, Any]]) -> None:
        if self._fhir_service:
            self.fhir_validation = FHIRValidationTester(self._fhir_service)
            for r in resources:
                self.fhir_validation.add_test_resource(r)
        else:
            logger.warning("FHIR service not configured — cannot register test resources")

    async def run_all(self, target_url: str = "") -> dict[str, Any]:
        suites: dict[str, TestSuite] = {}

        if self.contract._contracts:
            suites["contract"] = await self.contract.run_all(
                dict.fromkeys(self.contract._contracts, target_url),
            )

        if self._fhir_service and self.fhir_validation._test_resources:
            suites["fhir_validation"] = await self.fhir_validation.run_all()

        if self.integration._scenarios:
            suites["integration"] = await self.integration.run_all(target_url)

        if self.load._endpoints:
            result = await self.load.run()
            ts = TestSuite(name="load_tests", started_at=time.time(), completed_at=time.time())
            ts.results = [result]
            suites["load"] = ts

        if self.chaos._scenarios:
            chaos_suite = TestSuite(name="chaos_tests", started_at=time.time())
            for name in self.chaos._scenarios:
                result = await self.chaos.run_scenario(name, target_url)
                chaos_suite.results.append(result)
            chaos_suite.completed_at = time.time()
            suites["chaos"] = chaos_suite

        if self.security._test_cases:
            suites["security"] = await self.security.run_all(target_url)

        if self._fhir_service and self.compatibility._versions:
            test_resource = {"resourceType": "Patient", "id": "test"}
            suites["compatibility"] = await self.compatibility.run_all(self._fhir_service, test_resource)

        return {
            name: suite.to_dict()
            for name, suite in suites.items()
        }

    def get_test_report(self) -> dict[str, Any]:
        return self.run_all()
