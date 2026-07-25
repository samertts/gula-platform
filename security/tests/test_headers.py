from __future__ import annotations

from security.modules.headers.models import CORSConfig, CSPConfig, CSRFConfig, SanitizerConfig


class TestCSP:
    def test_csp_builder_directives(self, csp_builder):
        csp = csp_builder.build()
        assert "default-src 'self'" in csp
        assert "object-src 'none'" in csp
        assert "base-uri 'self'" in csp

    def test_csp_nonce_generation(self, csp_builder):
        nonce = csp_builder.generate_nonce()
        assert len(nonce) > 10
        csp_builder.add_nonce("script-src", nonce)
        csp = csp_builder.build()
        assert nonce in csp

    def test_csp_custom_directive(self, csp_builder):
        csp_builder.set_directive("report-uri", ["https://reports.gula.iq/csp"])
        csp = csp_builder.build()
        assert "report-uri https://reports.gula.iq/csp" in csp

    def test_csp_add_source(self, csp_builder):
        csp_builder.add_source("img-src", "https://images.gula.iq")
        assert "https://images.gula.iq" in csp_builder.build()

    def test_csp_remove_source(self, csp_builder):
        csp_builder.add_source("img-src", "https://test.gula.iq")
        csp_builder.remove_source("img-src", "https://test.gula.iq")
        assert "https://test.gula.iq" not in csp_builder.build()

    def test_csp_hash(self, csp_builder):
        hash_str = csp_builder.add_hash("script-src", "console.log('test')")
        assert hash_str.startswith("'sha256-")

    def test_csp_upgrade_insecure_requests(self, csp_builder):
        config = CSPConfig(upgrade_insecure_requests=True)
        builder = type(csp_builder)(config)
        csp = builder.build()
        assert "upgrade-insecure-requests" in csp

    def test_csp_reset(self, csp_builder):
        csp_builder.add_source("default-src", "https://example.com")
        csp_builder.reset()
        assert "https://example.com" not in csp_builder.build()


class TestSecurityHeaders:
    def test_security_headers_all_present(self, security_headers_manager):
        headers = security_headers_manager.get_all_headers()
        assert "Content-Security-Policy" in headers
        assert "Strict-Transport-Security" in headers
        assert "X-Content-Type-Options" in headers
        assert "X-Frame-Options" in headers

    def test_strict_transport_security_max_age(self, security_headers_manager):
        headers = security_headers_manager.get_all_headers()
        hsts = headers.get("Strict-Transport-Security", "")
        assert "max-age=31536000" in hsts

    def test_x_content_type_options(self, security_headers_manager):
        headers = security_headers_manager.get_all_headers()
        assert headers.get("X-Content-Type-Options") == "nosniff"

    def test_sensitive_paths_headers(self, security_headers_manager):
        headers = security_headers_manager.get_all_headers(sensitive=True)
        assert headers.get("X-Frame-Options") == "DENY"

    def test_referrer_policy(self, security_headers_manager):
        headers = security_headers_manager.get_all_headers()
        assert "Referrer-Policy" in headers

    def test_permissions_policy(self, security_headers_manager):
        headers = security_headers_manager.get_all_headers()
        assert "Permissions-Policy" in headers


class TestCORS:
    def test_cors_strict_origin_validation(self, cors_manager):
        headers = cors_manager.get_cors_headers("https://app.gula.iq", "GET")
        assert headers.get("Access-Control-Allow-Origin") == "https://app.gula.iq"

    def test_cors_block_unknown_origin(self, cors_manager):
        headers = cors_manager.get_cors_headers("https://evil.com", "GET")
        assert "Access-Control-Allow-Origin" not in headers

    def test_cors_credentials(self, cors_manager):
        headers = cors_manager.get_cors_headers("https://app.gula.iq", "GET")
        assert headers.get("Access-Control-Allow-Credentials") == "true"

    def test_cors_max_age(self, cors_manager):
        headers = cors_manager.get_cors_headers("https://app.gula.iq", "OPTIONS")
        assert "Access-Control-Max-Age" in headers


class TestCSRF:
    def test_csrf_token_generation_validation(self, csrf_protector):
        token = csrf_protector.generate_token()
        assert len(token) > 20
        assert csrf_protector.validate_token(token, token) is True

    def test_csrf_invalid_token(self, csrf_protector):
        token = csrf_protector.generate_token()
        assert csrf_protector.validate_token(token, "invalid-token") is False

    def test_csrf_token_uniqueness(self, csrf_protector):
        token1 = csrf_protector.generate_token()
        token2 = csrf_protector.generate_token()
        assert token1 != token2

    def test_csrf_header_name(self, csrf_protector):
        config = CSRFConfig(header_name="X-CSRF-Token")
        protector = type(csrf_protector)(config)
        assert protector._config.header_name == "X-CSRF-Token"


class TestInputSanitizer:
    def test_input_sanitization_xss(self, input_sanitizer):
        dangerous = "<script>alert('xss')</script>"
        sanitized = input_sanitizer.prevent_xss(dangerous, "html")
        assert "<script>" not in sanitized

    def test_input_sanitization_sqli(self, input_sanitizer):
        dangerous = "' OR 1=1; SELECT * FROM users"
        assert input_sanitizer.detect_sql_injection(dangerous) is True

    def test_input_sanitization_path_traversal(self, input_sanitizer):
        result = input_sanitizer.sanitize_path("../../../etc/passwd")
        assert result["valid"] is True
        assert "../../../" not in result["sanitized"]

    def test_sanitize_html_removes_scripts(self, input_sanitizer):
        cleaned = input_sanitizer.sanitize_html("<script>alert(1)</script><b>safe</b>")
        assert "<script>" not in cleaned
        assert "safe" in cleaned

    def test_validate_url_blocks_private_ip(self, input_sanitizer):
        result = input_sanitizer.validate_url("http://192.168.1.1/admin")
        assert result["valid"] is False

    def test_validate_url_valid(self, input_sanitizer):
        result = input_sanitizer.validate_url("https://api.gula.iq/v1/patients")
        assert result["valid"] is True

    def test_detect_command_injection(self, input_sanitizer):
        assert input_sanitizer.detect_command_injection("; rm -rf /") is True
        assert input_sanitizer.detect_command_injection("safe input") is False

    def test_prevent_open_redirect(self, input_sanitizer):
        result = input_sanitizer.prevent_open_redirect("https://evil.com/phish", ["gula.iq"])
        assert result["valid"] is False

    def test_sanitize_csv(self, input_sanitizer):
        assert input_sanitizer.sanitize_csv("=CMD") == "'=CMD"
        assert input_sanitizer.sanitize_csv("normal") == "normal"

    def test_sanitize_download_filename(self, input_sanitizer):
        cleaned = input_sanitizer.sanitize_download_filename("../../../etc/passwd")
        assert "/" not in cleaned
        assert ".." not in cleaned

    def test_prevent_xxe(self, input_sanitizer):
        xml = '<?xml version="1.0"?><!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><root>&xxe;</root>'
        cleaned = input_sanitizer.prevent_xxe(xml)
        assert "<!DOCTYPE" not in cleaned
        assert "<!ENTITY" not in cleaned


class TestMiddleware:
    def test_middleware_factory(self):
        from security.modules.headers.middleware import SecurityMiddlewareFactory
        factory = SecurityMiddlewareFactory()
        assert factory.get_csp_builder() is not None
        assert factory.get_headers_manager() is not None
        assert factory.get_cors_manager() is not None
        assert factory.get_csrf_protector() is not None
        assert factory.get_sanitizer() is not None

    def test_middleware_custom_processor(self):
        from security.modules.headers.middleware import SecurityMiddlewareFactory
        factory = SecurityMiddlewareFactory()
        called = []
        def processor(req, resp):
            called.append(True)
        factory.add_processor(processor)
        assert len(factory._custom_processors) == 1
