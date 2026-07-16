from __future__ import annotations

import hmac
import re
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class PolicyDecision(Enum):
    ALLOW = "allow"
    DENY = "deny"


@dataclass
class PolicyResult:
    decision: PolicyDecision
    policy_name: str
    reason: str = ""
    context: dict = field(default_factory=dict)


class BasePolicy:
    def __init__(self, name: str) -> None:
        self.name = name

    def evaluate(self, request: dict) -> PolicyResult:
        raise NotImplementedError


class RateLimitPolicy(BasePolicy):
    def __init__(self, name: str = "rate_limit") -> None:
        super().__init__(name)
        self._buckets: dict[str, list[float]] = {}

    def evaluate(self, request: dict) -> PolicyResult:
        client_id = request.get("client_id", "")
        endpoint = request.get("endpoint", "")
        max_requests = request.get("rate_limit_max", 60)
        window_seconds = request.get("rate_limit_window", 60)

        if not client_id:
            return PolicyResult(PolicyDecision.ALLOW, self.name)

        key = f"{client_id}:{endpoint}"
        now = time.time()
        bucket = self._buckets.get(key, [])
        bucket = [t for t in bucket if now - t < window_seconds]

        if len(bucket) >= max_requests:
            return PolicyResult(
                PolicyDecision.DENY,
                self.name,
                f"rate limit exceeded: {len(bucket)}/{max_requests} per {window_seconds}s",
            )

        bucket.append(now)
        self._buckets[key] = bucket
        return PolicyResult(PolicyDecision.ALLOW, self.name)

    def check_rate_limit(self, client_id: str, endpoint: str, max_requests: int = 60, window_seconds: int = 60) -> PolicyResult:
        return self.evaluate({
            "client_id": client_id,
            "endpoint": endpoint,
            "rate_limit_max": max_requests,
            "rate_limit_window": window_seconds,
        })


class QuotaPolicy(BasePolicy):
    def __init__(self, name: str = "quota") -> None:
        super().__init__(name)
        self._usage: dict[str, int] = {}

    def evaluate(self, request: dict) -> PolicyResult:
        client_id = request.get("client_id", "")
        max_quota = request.get("quota_max", 1000)

        if not client_id:
            return PolicyResult(PolicyDecision.ALLOW, self.name)

        current = self._usage.get(client_id, 0)
        if current >= max_quota:
            return PolicyResult(PolicyDecision.DENY, self.name, f"quota exceeded: {current}/{max_quota}")

        self._usage[client_id] = current + 1
        return PolicyResult(PolicyDecision.ALLOW, self.name)

    def check_quota(self, client_id: str, endpoint: str, max_quota: int = 1000) -> PolicyResult:
        return self.evaluate({"client_id": client_id, "endpoint": endpoint, "quota_max": max_quota})


class IPWhitelistPolicy(BasePolicy):
    def __init__(self, whitelist: list[str] | None = None, name: str = "ip_whitelist") -> None:
        super().__init__(name)
        self._whitelist = whitelist or []

    def evaluate(self, request: dict) -> PolicyResult:
        client_address = request.get("client_address", "")

        if not self._whitelist:
            return PolicyResult(PolicyDecision.ALLOW, self.name)

        if self._ip_matches(client_address):
            return PolicyResult(PolicyDecision.ALLOW, self.name)

        return PolicyResult(
            PolicyDecision.DENY,
            self.name,
            f"IP {client_address} not in whitelist",
        )

    def check_ip(self, client_address: str, whitelist: list[str] | None = None) -> PolicyResult:
        original = self._whitelist
        if whitelist is not None:
            self._whitelist = whitelist
        result = self.evaluate({"client_address": client_address})
        self._whitelist = original
        return result

    def _ip_matches(self, address: str) -> bool:
        for entry in self._whitelist:
            if "/" in entry:
                if self._ip_in_cidr(address, entry):
                    return True
            elif address == entry:
                return True
        return False

    def _ip_in_cidr(self, address: str, cidr: str) -> bool:
        try:
            import ipaddress
            return ipaddress.ip_address(address) in ipaddress.ip_network(cidr, strict=False)
        except ImportError:
            return address == cidr.split("/")[0]


class IPBlacklistPolicy(BasePolicy):
    def __init__(self, blacklist: list[str] | None = None, name: str = "ip_blacklist") -> None:
        super().__init__(name)
        self._blacklist = blacklist or []

    def evaluate(self, request: dict) -> PolicyResult:
        client_address = request.get("client_address", "")

        if self._ip_matches(client_address):
            return PolicyResult(
                PolicyDecision.DENY,
                self.name,
                f"IP {client_address} is blacklisted",
            )

        return PolicyResult(PolicyDecision.ALLOW, self.name)

    def check_ip(self, client_address: str, blacklist: list[str] | None = None) -> PolicyResult:
        original = self._blacklist
        if blacklist is not None:
            self._blacklist = blacklist
        result = self.evaluate({"client_address": client_address})
        self._blacklist = original
        return result

    def _ip_matches(self, address: str) -> bool:
        for entry in self._blacklist:
            if "/" in entry:
                try:
                    import ipaddress
                    if ipaddress.ip_address(address) in ipaddress.ip_network(entry, strict=False):
                        return True
                except ImportError:
                    pass
            elif address == entry:
                return True
        return False


class TimeRestrictionPolicy(BasePolicy):
    def __init__(self, name: str = "time_restriction") -> None:
        super().__init__(name)
        self._allowed_hours: list[int] = list(range(24))
        self._allowed_days: list[int] = list(range(7))

    def evaluate(self, request: dict) -> PolicyResult:
        now = datetime.utcnow()
        hour = now.hour
        day = now.weekday()

        if hour not in self._allowed_hours:
            return PolicyResult(
                PolicyDecision.DENY,
                self.name,
                f"access restricted at hour {hour}, allowed hours: {self._allowed_hours}",
            )
        if day not in self._allowed_days:
            return PolicyResult(
                PolicyDecision.DENY,
                self.name,
                f"access restricted on day {day}, allowed days: {self._allowed_days}",
            )
        return PolicyResult(PolicyDecision.ALLOW, self.name)

    def check_time(self, allowed_hours: list[int] | None = None, allowed_days: list[int] | None = None) -> PolicyResult:
        if allowed_hours is not None:
            self._allowed_hours = allowed_hours
        if allowed_days is not None:
            self._allowed_days = allowed_days
        return self.evaluate({})


class OAuth2Policy(BasePolicy):
    def __init__(self, name: str = "oauth2") -> None:
        super().__init__(name)
        self._token_validators: dict[str, Callable] = {}

    def evaluate(self, request: dict) -> PolicyResult:
        token = request.get("token", "")
        required_scopes = request.get("required_scopes", [])

        if not token:
            return PolicyResult(PolicyDecision.DENY, self.name, "no token provided")

        return self._validate_token(token, required_scopes)

    def validate_token(self, token: str, scopes: list[str] | None = None) -> PolicyResult:
        return self.evaluate({"token": token, "required_scopes": scopes or []})

    def register_validator(self, issuer: str, validator: Callable) -> None:
        self._token_validators[issuer] = validator

    def _validate_token(self, token: str, required_scopes: list[str]) -> PolicyResult:
        import json
        try:
            parts = token.split(".")
            if len(parts) != 3:
                return PolicyResult(PolicyDecision.DENY, self.name, "invalid token format")

            payload_b64 = parts[1]
            padding = 4 - len(payload_b64) % 4
            if padding != 4:
                payload_b64 += "=" * padding
            payload = json.loads(base64url_decode(payload_b64.encode()))

            exp = payload.get("exp", 0)
            if exp and time.time() > exp:
                return PolicyResult(PolicyDecision.DENY, self.name, "token expired")

            token_scopes = payload.get("scope", "").split() if isinstance(payload.get("scope"), str) else payload.get("scopes", [])
            for scope in required_scopes:
                if scope not in token_scopes:
                    return PolicyResult(PolicyDecision.DENY, self.name, f"missing required scope: {scope}")

            issuer = payload.get("iss", "")
            if issuer in self._token_validators:
                if not self._token_validators[issuer](token):
                    return PolicyResult(PolicyDecision.DENY, self.name, f"token validation failed for issuer {issuer}")

            return PolicyResult(PolicyDecision.ALLOW, self.name)

        except Exception as exc:
            return PolicyResult(PolicyDecision.DENY, self.name, f"token validation error: {exc}")


class mTLSPolicy(BasePolicy):
    def __init__(self, name: str = "mtls") -> None:
        super().__init__(name)
        self._trusted_cas: list[str] = []

    def evaluate(self, request: dict) -> PolicyResult:
        certificate = request.get("certificate", {})

        if not certificate:
            return PolicyResult(PolicyDecision.DENY, self.name, "no client certificate provided")

        return self._validate_cert(certificate)

    def validate_certificate(self, cert: dict) -> PolicyResult:
        return self.evaluate({"certificate": cert})

    def add_trusted_ca(self, ca_pem: str) -> None:
        self._trusted_cas.append(ca_pem)

    def _validate_cert(self, cert: dict) -> PolicyResult:
        valid_from = cert.get("valid_from", 0)
        valid_to = cert.get("valid_to", 0)
        now = time.time()

        if valid_from and now < valid_from:
            return PolicyResult(PolicyDecision.DENY, self.name, "certificate not yet valid")
        if valid_to and now > valid_to:
            return PolicyResult(PolicyDecision.DENY, self.name, "certificate expired")

        fingerprint = cert.get("fingerprint", "")
        if re.match(r"^[a-fA-F0-9]{2}(:[a-fA-F0-9]{2})+$", fingerprint):
            return PolicyResult(PolicyDecision.ALLOW, self.name)

        issuer = cert.get("issuer", "")
        if issuer and any(ca_name in issuer for ca_name in self._trusted_cas):
            return PolicyResult(PolicyDecision.ALLOW, self.name)

        return PolicyResult(PolicyDecision.DENY, self.name, "certificate not trusted")

    def set_trusted_cas(self, cas: list[str]) -> None:
        self._trusted_cas = cas


class APIKeyPolicy(BasePolicy):
    def __init__(self, name: str = "api_key") -> None:
        super().__init__(name)
        self._valid_keys: dict[str, dict] = {}

    def evaluate(self, request: dict) -> PolicyResult:
        api_key = request.get("api_key", "")
        expected_key = request.get("expected_key", "")

        if expected_key:
            if hmac.compare_digest(api_key, expected_key):
                return PolicyResult(PolicyDecision.ALLOW, self.name)
            return PolicyResult(PolicyDecision.DENY, self.name, "invalid API key")

        if api_key in self._valid_keys:
            key_data = self._valid_keys[api_key]
            if key_data.get("expires_at") and time.time() > key_data["expires_at"]:
                return PolicyResult(PolicyDecision.DENY, self.name, "API key expired")
            return PolicyResult(PolicyDecision.ALLOW, self.name)

        return PolicyResult(PolicyDecision.DENY, self.name, "invalid API key")

    def validate_api_key(self, key: str, expected_key: str) -> PolicyResult:
        return self.evaluate({"api_key": key, "expected_key": expected_key})

    def register_key(self, key: str, metadata: dict | None = None) -> None:
        self._valid_keys[key] = metadata or {}

    def revoke_key(self, key: str) -> None:
        self._valid_keys.pop(key, None)


class CompositePolicy(BasePolicy):
    def __init__(self, policies: list[BasePolicy] | None = None, name: str = "composite") -> None:
        super().__init__(name)
        self._policies = policies or []

    def add_policy(self, policy: BasePolicy) -> None:
        self._policies.append(policy)

    def remove_policy(self, policy_name: str) -> None:
        self._policies = [p for p in self._policies if p.name != policy_name]

    def evaluate(self, request: dict) -> PolicyResult:
        for policy in self._policies:
            result = policy.evaluate(request)
            if result.decision == PolicyDecision.DENY:
                return result
        return PolicyResult(PolicyDecision.ALLOW, self.name, "all policies passed")

    def evaluate_all(self, policies: list[BasePolicy]) -> PolicyResult:
        for policy in policies:
            result = policy.evaluate({})
            if result.decision == PolicyDecision.DENY:
                return result
        return PolicyResult(PolicyDecision.ALLOW, self.name, "all policies passed")


class GatewayPolicyEngine:
    def __init__(self) -> None:
        self._policies: dict[str, BasePolicy] = {}
        self._routes: dict[str, dict] = {}

    def register_policy(self, policy: BasePolicy) -> None:
        self._policies[policy.name] = policy

    def unregister_policy(self, name: str) -> None:
        self._policies.pop(name, None)

    def get_policy(self, name: str) -> BasePolicy | None:
        return self._policies.get(name)

    def list_policies(self) -> list[dict]:
        return [{"name": name, "type": type(policy).__name__} for name, policy in self._policies.items()]

    def evaluate(self, request: dict) -> PolicyResult:
        route_key = f"{request.get('method', 'GET')} {request.get('path', '')}"
        route_config = self._routes.get(route_key) or self._routes.get(f"* {request.get('path', '')}") or self._routes.get(f"{request.get('method', 'GET')} *") or self._routes.get("* *")
        if not route_config:
            return PolicyResult(PolicyDecision.DENY, "gateway", "no route configured")

        policy_names = route_config.get("policies", [])
        for name in policy_names:
            policy = self._policies.get(name)
            if policy:
                result = policy.evaluate(request)
                if result.decision == PolicyDecision.DENY:
                    return result

        return PolicyResult(PolicyDecision.ALLOW, "gateway", "request allowed")

    def register_route(self, method: str, path: str, config: dict) -> None:
        key = f"{method.upper()} {path}"
        self._routes[key] = config

    def unregister_route(self, method: str, path: str) -> None:
        key = f"{method.upper()} {path}"
        self._routes.pop(key, None)

    def list_routes(self) -> list[dict]:
        return [
            {"method": key.split(" ")[0], "path": key.split(" ", 1)[1], "config": config}
            for key, config in self._routes.items()
        ]


def base64url_decode(data: bytes) -> bytes:
    import base64
    rem = len(data) % 4
    if rem:
        data += b"=" * (4 - rem)
    return base64.urlsafe_b64decode(data)
