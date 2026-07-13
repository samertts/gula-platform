from __future__ import annotations

from typing import Any

from backend.app.engineering.generators.base import BaseGenerator, GenerateResult


class PerformanceTestGenerator(BaseGenerator):
    def generate(self, **kwargs: Any) -> GenerateResult:
        module = kwargs.get("module", "app")
        endpoint = kwargs.get("endpoint", "/api/v1/items")
        concurrency = kwargs.get("concurrency", 10)
        rounds = kwargs.get("rounds", 3)

        content = f'''"""Performance tests for {module}."""
from __future__ import annotations

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor

import pytest


@pytest.mark.performance
class Test{module.title().replace("_", "")}Performance:
    @pytest.fixture
    def base_url(self) -> str:
        return "http://test"

    @pytest.mark.slow
    def test_endpoint_latency(self, base_url: str):
        """Measure endpoint response time."""
        import httpx
        start = time.monotonic()
        response = httpx.get(f"{{base_url}}{endpoint}")
        elapsed = (time.monotonic() - start) * 1000
        assert response.status_code < 500
        assert elapsed < 2000, f"Response took {{elapsed:.0f}}ms (threshold: 2000ms)"

    @pytest.mark.slow
    def test_concurrent_requests(self, base_url: str):
        """Test concurrency handling."""
        import httpx

        def request(n: int) -> float:
            start = time.monotonic()
            try:
                r = httpx.get(f"{{base_url}}{endpoint}", timeout=30)
                return (time.monotonic() - start) * 1000
            except Exception:
                return -1

        with ThreadPoolExecutor(max_workers={concurrency}) as pool:
            latencies = list(pool.map(request, range({rounds})))

        avg_latency = sum(l for l in latencies if l > 0) / max(len([l for l in latencies if l > 0]), 1)
        failures = sum(1 for l in latencies if l < 0)
        assert failures < {concurrency} // 2, f"{{failures}} requests failed"
        assert avg_latency < 5000, f"Average latency {{avg_latency:.0f}}ms (threshold: 5000ms)"

    @pytest.mark.slow
    def test_throughput(self, base_url: str):
        """Measure request throughput."""
        import httpx

        start = time.monotonic()
        count = 0
        while time.monotonic() - start < 2.0:
            try:
                r = httpx.get(f"{{base_url}}{endpoint}", timeout=30)
                if r.status_code < 500:
                    count += 1
            except Exception:
                pass
        throughput = count / 2.0
        assert throughput > 10, f"Throughput {{throughput:.0f}} req/s (threshold: 10 req/s)"
'''
        self._write(f"test_performance_{module}.py", content)
        return self._result


class SecurityTestGenerator(BaseGenerator):
    def generate(self, **kwargs: Any) -> GenerateResult:
        module = kwargs.get("module", "app")
        auth_token = kwargs.get("auth_token", "test-token")

        content = f'''"""Security tests for {module}."""
from __future__ import annotations

import pytest


@pytest.mark.security
class Test{module.title().replace("_", "")}Security:
    def test_sql_injection(self, client):
        """Verify SQL injection is blocked."""
        payloads = [
            "' OR '1'='1",
            "'; DROP TABLE users; --",
            "' UNION SELECT * FROM users; --",
            "1; SELECT * FROM admin;",
        ]
        for payload in payloads:
            response = client.get(f"/api/search?q={{payload}}")
            assert response.status_code != 500

    def test_xss_protection(self, client):
        """Verify XSS payloads are sanitized."""
        payloads = [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert(1)>",
            "javascript:alert(1)",
        ]
        for payload in payloads:
            response = client.post("/api/feedback", json={{"message": payload}})
            assert response.status_code != 500

    def test_unauthorized_access(self, client):
        """Verify protected endpoints reject unauthenticated requests."""
        protected = [
            "/api/admin",
            "/api/users",
            "/api/settings",
        ]
        for path in protected:
            response = client.get(path)
            assert response.status_code in (401, 403), f"{{path}} returned {{response.status_code}}"

    def test_csrf_protection(self, client):
        """Verify CSRF protection is active."""
        response = client.post(
            "/api/transfer",
            json={{"amount": 100}},
            headers={{"Origin": "https://evil.com"}},
        )
        assert response.status_code in (403, 422)

    def test_rate_limiting(self, client):
        """Verify rate limiting is enforced."""
        responses = []
        for _ in range(100):
            response = client.get("/api/public")
            responses.append(response.status_code)
        assert 429 in responses, "Rate limiting not detected"

    def test_jwt_token_validation(self, client):
        """Verify invalid JWT tokens are rejected."""
        tokens = [
            "invalid-token",
            "eyJ.eyJ.eyJ",
            "",
        ]
        for token in tokens:
            response = client.get(
                "/api/protected",
                headers={{"Authorization": f"Bearer {{token}}"}},
            )
            assert response.status_code in (401, 403)

    def test_mass_assignment(self, client):
        """Verify mass assignment protection."""
        response = client.post(
            "/api/users",
            json={{"username": "test", "is_admin": True, "role": "superuser"}},
        )
        data = response.json()
        assert data.get("is_admin") is not True
'''
        self._write(f"test_security_{module}.py", content)
        return self._result
