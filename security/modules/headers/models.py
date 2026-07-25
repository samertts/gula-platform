from __future__ import annotations

from pydantic import BaseModel, Field


class CSPConfig(BaseModel):
    enabled: bool = True
    report_only: bool = False
    report_uri: str = ""
    report_to: str = ""
    enforce_trusted_types: bool = True
    strict_csp: bool = True
    upgrade_insecure_requests: bool = True


class CORSConfig(BaseModel):
    enabled: bool = True
    allow_origins: list[str] = Field(default_factory=list)
    allow_methods: list[str] = Field(default_factory=lambda: ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
    allow_headers: list[str] = Field(default_factory=lambda: [
        "Authorization", "Content-Type", "X-Requested-By", "X-CSRF-Token",
    ])
    expose_headers: list[str] = Field(default_factory=list)
    allow_credentials: bool = True
    max_age: int = 3600


class CSRFConfig(BaseModel):
    enabled: bool = True
    cookie_name: str = "csrf_token"
    header_name: str = "X-CSRF-Token"
    cookie_secure: bool = True
    cookie_samesite: str = "strict"
    token_length: int = 32
    exempt_methods: list[str] = Field(default_factory=lambda: ["GET", "HEAD", "OPTIONS"])


class HeaderConfig(BaseModel):
    hsts_max_age: int = 31536000
    hsts_include_subdomains: bool = True
    hsts_preload: bool = False
    x_frame_options: str = "DENY"
    referrer_policy: str = "strict-origin-when-cross-origin"
    permissions_policy: dict[str, list[str]] = Field(default_factory=lambda: {
        "camera": [],
        "microphone": [],
        "geolocation": [],
        "display-capture": [],
        "fullscreen": ["self"],
    })


class SecurityHeadersConfig(BaseModel):
    csp: CSPConfig = Field(default_factory=CSPConfig)
    cors: CORSConfig = Field(default_factory=CORSConfig)
    csrf: CSRFConfig = Field(default_factory=CSRFConfig)
    headers: HeaderConfig = Field(default_factory=HeaderConfig)


class SanitizerConfig(BaseModel):
    strip_html: bool = True
    detect_sql_injection: bool = True
    prevent_xss: bool = True
    prevent_ssrf: bool = True
    prevent_command_injection: bool = True
    prevent_path_traversal: bool = True
    prevent_xxe: bool = True
    prevent_open_redirect: bool = True
    validate_file_uploads: bool = True
    max_upload_size_mb: int = 10
    allowed_mime_types: list[str] = Field(default_factory=lambda: [
        "image/jpeg", "image/png", "image/gif", "image/webp",
        "application/pdf",
        "text/plain", "text/csv",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ])
