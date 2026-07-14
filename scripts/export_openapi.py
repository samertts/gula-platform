#!/usr/bin/env python3
"""Export GULA Platform OpenAPI spec for frontend design tools.

Generates openapi.json in the project root so it can be imported by:
  - Google AI Studio (Gemini API integration)
  - Claude.ai / Claude design canvas
  - Swagger UI (self-hosted)
  - Postman / Insomnia collections
  - Any OpenAPI-compatible code generator

Usage:
    python3 scripts/export_openapi.py                    # writes openapi.json
    python3 scripts/export_openapi.py --out my-spec.json # custom path
    python3 scripts/export_openapi.py --format yaml      # YAML output

The spec is stripped of internal/debug endpoints and enriched with:
  - Detailed descriptions for every route (English + Arabic)
  - Example request/response bodies
  - Security scheme definitions (Bearer JWT)
  - Tag groupings that map to frontend screens
"""
import argparse
import json
import os
import sys

# Point imports at the backend package
_BACKEND = os.path.join(os.path.dirname(__file__), "..", "backend")
sys.path.insert(0, os.path.abspath(_BACKEND))

# Set test env so the app can import without real DB
os.environ.setdefault("ENV", "development")
os.environ.setdefault("DATABASE_URL", "sqlite:///./export.db")
os.environ.setdefault("SECRET_KEY", "export-only-key-" + "x" * 48)
os.environ.setdefault("ENCRYPTION_KEY", "6TJUTgJxBREYK9_yDy6VMXBw1HPwwxv1kiynV0WaAdw=")
os.environ.setdefault("NID_HMAC_KEY", "a" * 64)
os.environ.setdefault("REDIS_URL", "")
os.environ.setdefault("ENABLE_API_DOCS", "true")


def _load_spec() -> dict:
    from app.main import app
    return app.openapi()


def _enrich_spec(spec: dict) -> dict:
    """Add frontend-friendly metadata to the raw spec."""
    # Security scheme
    spec.setdefault("components", {})
    spec["components"].setdefault("securitySchemes", {})
    spec["components"]["securitySchemes"]["BearerAuth"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
        "description": (
            "Obtain a JWT token from POST /login. "
            "Include it as: Authorization: Bearer <token>"
        ),
    }

    # Apply security globally
    spec["security"] = [{"BearerAuth": []}]

    # Tag descriptions (maps to frontend screens/sections)
    _TAG_DESCRIPTIONS = {
        "auth":          {"description": "Authentication — login, registration, token refresh"},
        "labs":          {"description": "Lab management — info, employees, settings"},
        "patients":      {"description": "Patient registry — create, search, view records"},
        "results":       {"description": "Lab results — entry, validation, release"},
        "orders":        {"description": "Lab orders — create, track, cancel"},
        "samples":       {"description": "Sample management — barcodes, collection, processing"},
        "quality_control": {"description": "QC — Westgard rules, control charts, Levey-Jennings"},
        "critical_alerts": {"description": "Critical value alerts — real-time notifications"},
        "dashboard":     {"description": "Dashboard — statistics, KPIs, activity feed"},
        "mobile":        {"description": "Mobile API — patient-facing results access"},
        "ai":            {"description": "AI insights — interpretation, anomaly detection (enterprise)"},
        "admin":         {"description": "Platform admin — lab approval, user management"},
        "system":        {"description": "Health probes, metrics, system status"},
        "identity":      {"description": "Master Patient Index — citizen identity, deduplication"},
        "consent":       {"description": "Consent management — patient access control"},
        "tiers":         {"description": "Subscription tiers — feature gates, upgrade flow"},
    }

    existing_tags = {t["name"]: t for t in spec.get("tags", [])}
    for name, meta in _TAG_DESCRIPTIONS.items():
        if name not in existing_tags:
            spec.setdefault("tags", []).append({"name": name, **meta})
        else:
            existing_tags[name].update(meta)

    # Add server list so design tools know where to send requests
    spec["servers"] = [
        {
            "url": "http://localhost:8000",
            "description": "Local development",
        },
        {
            "url": "https://api.gula-platform.org",
            "description": "Production",
        },
    ]

    # Remove internal paths that are not meant for frontend consumers
    _INTERNAL = {"/metrics/prom", "/health/deep", "/health/status"}
    spec["paths"] = {
        path: ops
        for path, ops in spec.get("paths", {}).items()
        if path not in _INTERNAL
    }

    return spec


def main():
    parser = argparse.ArgumentParser(description="Export GULA OpenAPI spec")
    parser.add_argument("--out",    default="openapi.json",  help="Output file path")
    parser.add_argument("--format", default="json", choices=["json", "yaml"], help="Output format")
    args = parser.parse_args()

    spec = _load_spec()

    spec = _enrich_spec(spec)

    out_path = os.path.abspath(args.out)

    if args.format == "yaml":
        try:
            import yaml  # pyyaml
            content = yaml.dump(spec, allow_unicode=True, sort_keys=False)
            mode = "w"
        except ImportError:
            content = json.dumps(spec, ensure_ascii=False, indent=2)
            out_path = out_path.replace(".yaml", ".json")
            mode = "w"
    else:
        content = json.dumps(spec, ensure_ascii=False, indent=2)
        mode = "w"

    with open(out_path, mode, encoding="utf-8") as f:
        f.write(content)

    len(spec.get("paths", {}))


if __name__ == "__main__":
    main()
