from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.middleware import SecurityHeadersMiddleware


def test_security_headers_disable_hardware_and_sensitive_browser_features() -> None:
    app = FastAPI()
    app.add_middleware(SecurityHeadersMiddleware)

    @app.get("/public")
    def public() -> dict[str, bool]:
        return {"ok": True}

    response = TestClient(app).get("/public")

    assert response.status_code == 200
    assert response.headers["Permissions-Policy"] == (
        "camera=(), microphone=(), geolocation=(), payment=(), "
        "usb=(), bluetooth=(), serial=()"
    )
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Cross-Origin-Resource-Policy"] == "same-site"
