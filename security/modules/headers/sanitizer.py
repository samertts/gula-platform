from __future__ import annotations

import csv
import html
import ipaddress
import json
import logging
import os
import re
import secrets
import struct
from io import BytesIO
from typing import Any, BinaryIO
from urllib.parse import urlparse

from security.modules.headers.models import SanitizerConfig

logger = logging.getLogger("gula.security.modules.headers.sanitizer")

_SCRIPT_PATTERN = re.compile(r"<script[^>]*>.*?</script>", re.IGNORECASE | re.DOTALL)
_ON_EVENT_PATTERN = re.compile(r"\bon\w+\s*=", re.IGNORECASE)
_JAVASCRIPT_PATTERN = re.compile(r"javascript\s*:", re.IGNORECASE)
_SQL_PATTERNS = [
    re.compile(r"('|--|/\*|;)\s*(or|and|union|select|insert|update|delete|drop|alter|exec|execute|sp_|xp_)", re.IGNORECASE),
    re.compile(r"union\s+(\s*all\s+)?select", re.IGNORECASE),
    re.compile(r"information_schema", re.IGNORECASE),
]
_PATH_TRAVERSAL_PATTERN = re.compile(r"(\.\.(%[0-9a-fA-F]{2})?/?)")
_COMMAND_INJECTION_CHARS = set("&|;`$(){}[]!<>")
_SSRF_BLOCKED_IPS: list[ipaddress.IPv4Network | ipaddress.IPv6Network] = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]


class InputSanitizer:
    def __init__(self, config: SanitizerConfig | None = None) -> None:
        self._config = config or SanitizerConfig()

    def sanitize_html(self, value: str) -> str:
        if not self._config.strip_html:
            return value

        cleaned = _SCRIPT_PATTERN.sub("", value)
        cleaned = _ON_EVENT_PATTERN.sub("", cleaned)
        cleaned = _JAVASCRIPT_PATTERN.sub("", cleaned)

        cleaned = html.escape(cleaned, quote=True)

        cleaned = cleaned.replace("&amp;", "&")
        cleaned = re.sub(r"&lt;(/?)(\w+)&gt;", r"<\1\2>", cleaned)

        allowed_tags = {
            "b", "i", "u", "em", "strong", "p", "br", "ul", "ol", "li",
            "span", "div", "table", "tr", "td", "th", "thead", "tbody",
            "h1", "h2", "h3", "h4", "h5", "h6", "hr", "pre", "code", "blockquote",
        }

        def _clean_tag(m: re.Match) -> str:
            tag = m.group(0)
            tag_name_match = re.match(r"</?(\w+)", tag)
            if tag_name_match:
                tag_name = tag_name_match.group(1).lower()
                if tag_name in allowed_tags:
                    return re.sub(r'\s*\w+\s*=\s*"[^"]*"', "", tag)
            return ""

        cleaned = re.sub(r"</?(\w+)[^>]*>", _clean_tag, cleaned)
        return cleaned

    def detect_sql_injection(self, value: str) -> bool:
        if not self._config.detect_sql_injection:
            return False
        return any(pattern.search(value) for pattern in _SQL_PATTERNS)

    def prevent_xss(self, value: str, context: str = "html") -> str:
        if not self._config.prevent_xss:
            return value

        if context == "html":
            return html.escape(value, quote=True)
        if context == "attribute":
            return html.escape(value, quote=True).replace("&gt;", ">").replace("&lt;", "<")
        if context == "javascript":
            return json.dumps(value, ensure_ascii=False)
        if context == "url":
            from urllib.parse import quote
            return quote(value, safe="")
        if context == "css":
            return re.sub(r"[^a-zA-Z0-9\s\-_.#]", "", value)

        return html.escape(value, quote=True)

    def validate_url(self, url: str, allowed_schemes: set[str] | None = None) -> dict[str, Any]:
        if not self._config.prevent_ssrf:
            return {"valid": True, "sanitized": url}

        schemes = allowed_schemes or {"https", "http", "ftp", "ftps"}
        result: dict[str, Any] = {"valid": False, "sanitized": url, "reason": ""}

        try:
            parsed = urlparse(url)
        except Exception:
            result["reason"] = "malformed_url"
            return result

        if not parsed.scheme:
            result["reason"] = "missing_scheme"
            return result
        if parsed.scheme.lower() not in schemes:
            result["reason"] = f"scheme_not_allowed: {parsed.scheme}"
            return result

        hostname = parsed.hostname or ""
        try:
            addr = ipaddress.ip_address(hostname)
            for blocked in _SSRF_BLOCKED_IPS:
                if addr in blocked or (isinstance(blocked, ipaddress.IPv4Network) and addr in blocked):
                    result["reason"] = "private_ip_blocked"
                    return result
        except ValueError:
            pass

        if hostname in {"localhost", "127.0.0.1", "0.0.0.0", "::1", "[::1]"}:
            result["reason"] = "localhost_blocked"
            return result

        try:
            addrs = set()
            try:
                import socket
                for info in socket.getaddrinfo(hostname, 80):
                    ip_str = info[4][0]
                    try:
                        addrs.add(ipaddress.ip_address(ip_str))
                    except ValueError:
                        pass
            except Exception:
                pass

            for addr in addrs:
                for blocked in _SSRF_BLOCKED_IPS:
                    if isinstance(blocked, (ipaddress.IPv4Network, ipaddress.IPv6Network)):
                        if addr in blocked:
                            result["reason"] = "resolved_to_private_ip"
                            return result
        except Exception:
            pass

        result["valid"] = True
        return result

    def detect_command_injection(self, value: str) -> bool:
        if not self._config.prevent_command_injection:
            return False

        if any(c in value for c in _COMMAND_INJECTION_CHARS):
            return True

        cmd_patterns = [
            r"\b(cmd|powershell|sh|bash|zsh|ksh|dash)\b",
            r"\b(exec|system|popen|subprocess|os\.system|os\.popen)\s*\(",
            r"`[^`]*`",
            r"\$\([^)]+\)",
            r"\|.*\b(wget|curl|nc|netcat|bash|sh|python|perl|ruby)\b",
        ]
        return any(re.search(p, value, re.IGNORECASE) for p in cmd_patterns)

    def sanitize_path(self, path: str, base_dir: str = "") -> dict[str, Any]:
        if not self._config.prevent_path_traversal:
            return {"valid": True, "sanitized": path}

        result: dict[str, Any] = {"valid": False, "sanitized": path, "reason": ""}

        if _PATH_TRAVERSAL_PATTERN.search(path):
            result["reason"] = "path_traversal_detected"
            result["sanitized"] = re.sub(r"\.\.(/|\\)", "", path)
            result["valid"] = True
            return result

        normalized = os.path.normpath(path)
        if base_dir:
            full_path = os.path.normpath(os.path.join(base_dir, normalized))
            if not full_path.startswith(os.path.normpath(base_dir)):
                result["reason"] = "path_escape_detected"
                return result
            result["sanitized"] = full_path

        result["valid"] = True
        result["sanitized"] = normalized
        return result

    def prevent_xxe(self, xml_content: str) -> str:
        if not self._config.prevent_xxe:
            return xml_content

        cleaned = re.sub(r"<!DOCTYPE[^>]*\[.*?\]>", "", xml_content, flags=re.IGNORECASE | re.DOTALL)
        cleaned = re.sub(r"<!ENTITY\s+\S+\s+SYSTEM\s+\S+\s*>", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"<!ENTITY\s+\S+\s+PUBLIC\s+\S+\s+\S+\s*>", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"<!ENTITY\s+\S+\s+[^>]*>", "", cleaned, flags=re.IGNORECASE)
        return cleaned

    def prevent_open_redirect(self, redirect_url: str, allowed_domains: list[str] | None = None) -> dict[str, Any]:
        if not self._config.prevent_open_redirect:
            return {"valid": True, "sanitized": redirect_url}

        result: dict[str, Any] = {"valid": False, "sanitized": redirect_url, "reason": ""}

        try:
            parsed = urlparse(redirect_url)
        except Exception:
            result["reason"] = "malformed_url"
            return result

        if not parsed.netloc:
            result["valid"] = True
            return result

        if parsed.scheme and parsed.scheme not in {"https", "http"}:
            result["reason"] = "invalid_scheme"
            return result

        if allowed_domains:
            hostname = parsed.hostname or ""
            for domain in allowed_domains:
                if hostname == domain or hostname.endswith(f".{domain}"):
                    result["valid"] = True
                    return result
            result["reason"] = f"domain_not_allowed: {hostname}"
            return result

        result["valid"] = True
        return result

    def validate_file_upload(self, file_data: bytes, filename: str, content_type: str) -> dict[str, Any]:
        if not self._config.validate_file_uploads:
            return {"valid": True, "reason": ""}

        result: dict[str, Any] = {"valid": False, "reason": ""}

        ext = os.path.splitext(filename)[1].lower() if filename else ""
        dangerous_extensions = {
            ".exe", ".bat", ".cmd", ".com", ".sh", ".bash", ".zsh",
            ".vbs", ".ps1", ".js", ".jse", ".wsf", ".wsh",
            ".jar", ".class", ".php", ".phtml", ".php3", ".php4", ".php5",
            ".asp", ".aspx", ".cer", ".cfm", ".shtml",
            ".dll", ".sys", ".scr", ".cpl", ".msi", ".msp",
        }
        if ext in dangerous_extensions:
            result["reason"] = f"extension_not_allowed: {ext}"
            return result

        size_mb = len(file_data) / (1024 * 1024)
        if size_mb > self._config.max_upload_size_mb:
            result["reason"] = f"file_too_large: {size_mb:.2f}MB > {self._config.max_upload_size_mb}MB"
            return result

        mime_map: dict[str, list[bytes]] = {
            "image/jpeg": [b"\xff\xd8\xff"],
            "image/png": [b"\x89PNG\r\n\x1a\n"],
            "image/gif": [b"GIF87a", b"GIF89a"],
            "image/webp": [b"RIFF"],
            "application/pdf": [b"%PDF"],
            "application/zip": [b"PK\x03\x04"],
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [b"PK\x03\x04"],
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [b"PK\x03\x04"],
        }

        if content_type in mime_map:
            matched = any(file_data.startswith(sig) for sig in mime_map[content_type])
            if not matched:
                result["reason"] = f"magic_bytes_mismatch_for: {content_type}"
                return result

        if self._config.allowed_mime_types and content_type not in self._config.allowed_mime_types:
            result["reason"] = f"mime_type_not_allowed: {content_type}"
            return result

        result["valid"] = True
        return result

    def sanitize_download_filename(self, filename: str) -> str:
        cleaned = re.sub(r'[<>:"/\\|?*]', "_", filename)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        cleaned = re.sub(r"\.\.+", ".", cleaned)
        if not cleaned:
            cleaned = "download"
        return cleaned

    def sanitize_csv(self, value: str) -> str:
        if value.startswith(("=", "+", "-", "@")):
            return f"'{value}"
        return value

    def sanitize_json(self, value: str) -> str:
        try:
            parsed = json.loads(value)
            if isinstance(parsed, dict):
                sanitized = {}
                for k, v in parsed.items():
                    if isinstance(v, str):
                        sanitized[k] = html.escape(v, quote=True)
                    else:
                        sanitized[k] = v
                return json.dumps(sanitized, ensure_ascii=False)
            return value
        except (json.JSONDecodeError, TypeError):
            return value

    def sanitize(self, value: Any, context: str = "html") -> Any:
        if isinstance(value, str):
            value = self.prevent_xss(value, context)
            if self._config.detect_sql_injection and self.detect_sql_injection(value):
                logger.warning("SQL injection pattern detected in input")
            if self._config.prevent_command_injection and self.detect_command_injection(value):
                logger.warning("Command injection pattern detected in input")
            return value
        if isinstance(value, dict):
            return {k: self.sanitize(v, context) for k, v in value.items()}
        if isinstance(value, list):
            return [self.sanitize(v, context) for v in value]
        return value
