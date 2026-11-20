from __future__ import annotations

from types import SimpleNamespace
from urllib.parse import parse_qs, urlparse

import pytest
from app.localization.delivery import create_router as create_delivery_router
from app.localization.preferences import (
    InMemoryPreferenceStore,
)
from app.localization.preferences import (
    create_router as create_preference_router,
)
from fastapi import FastAPI
from fastapi.testclient import TestClient

from .conftest import make_pack


@pytest.fixture()
def api_client(registry, signing_key, pack_manager):
    pack_bytes = make_pack(registry, signing_key)
    store = InMemoryPreferenceStore()
    app = FastAPI()
    app.include_router(
        create_delivery_router(
            registry=registry, pack_manager=pack_manager, pack_store={"fa": pack_bytes}
        )
    )
    app.include_router(
        create_preference_router(
            registry=registry,
            pack_manager=pack_manager,
            preference_store_provider=lambda: store,
            current_user_provider=lambda: SimpleNamespace(id=1, lab_id=1),
        )
    )
    return TestClient(app), store, pack_bytes


def test_list_languages_exposes_five_core_entries(api_client):
    client, _, _ = api_client
    response = client.get("/api/v1/localization/languages")
    assert response.status_code == 200
    payload = response.json()
    core = [item for item in payload["languages"] if item["classification"] == "core"]
    assert len(core) == 5
    assert payload["fallback_language"] == "en"


def test_manifest_endpoint_returns_signed_manifest(api_client):
    client, _, _ = api_client
    response = client.get("/api/v1/localization/languages/fa/manifest")
    assert response.status_code == 200
    assert response.json()["signature"]
    assert response.json()["approval_status"] == "synthetic_test_only"


def test_download_policy_blocks_data_saver(api_client):
    client, _, _ = api_client
    response = client.post(
        "/api/v1/localization/language-packs/fa/download",
        json={"data_saver_enabled": True, "allow_metered_network": False},
    )
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "DOWNLOAD_BLOCKED_BY_DATA_SAVER"


def test_download_status_and_short_lived_content(api_client):
    client, _, pack_bytes = api_client
    response = client.post("/api/v1/localization/language-packs/fa/download", json={})
    assert response.status_code == 200
    payload = response.json()
    assert payload["expected_size"] == len(pack_bytes)
    assert payload["signature_metadata"]["signature_present"] is True

    parsed = urlparse(payload["download_url"])
    query = parse_qs(parsed.query)
    status_response = client.get(
        f"/api/v1/localization/downloads/{payload['download_id']}",
        params={"token": query["token"][0]},
    )
    assert status_response.status_code == 200
    assert status_response.json()["status"] == "AVAILABLE"

    content = client.get(parsed.path, params={"token": query["token"][0]})
    assert content.status_code == 200
    assert content.content == pack_bytes
    assert content.headers["cache-control"] == "no-store"

    invalid = client.get(parsed.path, params={"token": "wrong-token"})
    assert invalid.status_code == 403
    assert invalid.json()["detail"]["code"] == "INVALID_DOWNLOAD_TOKEN"


def test_preference_stays_english_until_pack_ready(api_client, pack_manager, registry, signing_key):
    client, store, _ = api_client
    catalogs = {
        f"catalogs/{name}.json": b'{"ui.home": "Synthetic"}'
        for name in registry.require("ckb").catalogs
    }
    ckb_pack = make_pack(registry, signing_key, language_id="ckb", files=catalogs)
    response = client.put(
        "/api/v1/users/me/preferences/language",
        json={"preferred_language": "ckb", "fallback_language": "en", "auto_download": True},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["preferred_language"] == "ckb"
    assert payload["effective_language"] == "en"
    assert payload["download_required"] is True
    assert store.records[(1, 1)]["language"] == "ckb"

    pack_manager.install("ckb", ckb_pack)
    second = client.put(
        "/api/v1/users/me/preferences/language",
        json={"preferred_language": "ckb", "fallback_language": "en", "auto_download": False},
    )
    assert second.json()["effective_language"] == "ckb"
    assert second.json()["download_required"] is False


def test_preference_rejects_blocked_downloadable_language(api_client):
    client, _, _ = api_client
    response = client.put(
        "/api/v1/users/me/preferences/language",
        json={"preferred_language": "fa", "fallback_language": "en", "auto_download": True},
    )
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "LANGUAGE_NOT_ACTIVE"


def test_preference_rejects_pending_language(api_client):
    client, _, _ = api_client
    response = client.put(
        "/api/v1/users/me/preferences/language",
        json={
            "preferred_language": "PENDING_SYRIAC",
            "fallback_language": "en",
            "auto_download": False,
        },
    )
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "LANGUAGE_NOT_ACTIVE"


def test_preference_rejects_non_english_fallback(api_client):
    client, _, _ = api_client
    response = client.put(
        "/api/v1/users/me/preferences/language",
        json={"preferred_language": "ar", "fallback_language": "ar", "auto_download": False},
    )
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "INVALID_FALLBACK_LANGUAGE"


def test_unknown_language_is_not_ready(api_client):
    client, _, _ = api_client
    unregistered = client.get("/api/v1/localization/languages/NOT_A_LANGUAGE/manifest")
    assert unregistered.status_code == 404
    assert unregistered.json()["detail"]["code"] == "LANGUAGE_NOT_FOUND"

    pending = client.get("/api/v1/localization/languages/PENDING_SYRIAC/manifest")
    assert pending.status_code == 404
    assert pending.json()["detail"]["code"] == "PACK_NOT_AVAILABLE"


def test_download_progress_resumes_from_byte_range(api_client):
    client, _, pack_bytes = api_client
    response = client.post("/api/v1/localization/language-packs/fa/download", json={})
    payload = response.json()
    parsed = urlparse(payload["download_url"])
    token = parse_qs(parsed.query)["token"][0]

    partial = client.get(parsed.path, params={"token": token}, headers={"Range": "bytes=0-9"})
    assert partial.status_code == 206
    assert partial.content == pack_bytes[:10]
    progress = client.get(
        f"/api/v1/localization/downloads/{payload['download_id']}", params={"token": token}
    ).json()
    assert progress["status"] == "DOWNLOADING"
    assert progress["downloaded_bytes"] == 10
    assert progress["resumable"] is True

    remainder = client.get(parsed.path, params={"token": token}, headers={"Range": "bytes=10-"})
    assert remainder.content == pack_bytes[10:]
    complete = client.get(
        f"/api/v1/localization/downloads/{payload['download_id']}", params={"token": token}
    ).json()
    assert complete["status"] == "COMPLETE"
    assert complete["progress"] == 1.0
    assert complete["resumable"] is False


def test_download_can_be_cancelled(api_client):
    client, _, _ = api_client
    response = client.post("/api/v1/localization/language-packs/fa/download", json={})
    payload = response.json()
    parsed = urlparse(payload["download_url"])
    token = parse_qs(parsed.query)["token"][0]

    cancelled = client.delete(
        f"/api/v1/localization/downloads/{payload['download_id']}", params={"token": token}
    )
    assert cancelled.status_code == 200
    assert cancelled.json()["code"] == "DOWNLOAD_CANCELLED"
    assert (
        client.get(
            f"/api/v1/localization/downloads/{payload['download_id']}", params={"token": token}
        ).status_code
        == 404
    )


def test_tail_only_range_never_marks_download_complete(api_client):
    client, _, pack_bytes = api_client
    payload = client.post("/api/v1/localization/language-packs/fa/download", json={}).json()
    parsed = urlparse(payload["download_url"])
    token = parse_qs(parsed.query)["token"][0]
    tail = client.get(
        parsed.path,
        params={"token": token},
        headers={"Range": f"bytes={len(pack_bytes) - 5}-"},
    )
    assert tail.status_code == 206
    progress = client.get(
        f"/api/v1/localization/downloads/{payload['download_id']}", params={"token": token}
    ).json()
    assert progress["status"] == "DOWNLOADING"
    assert progress["downloaded_bytes"] == 0
    assert progress["resumable"] is True


def test_progress_requires_download_token(api_client):
    client, _, _ = api_client
    download_id = client.post("/api/v1/localization/language-packs/fa/download", json={}).json()[
        "download_id"
    ]
    response = client.get(f"/api/v1/localization/downloads/{download_id}")
    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "INVALID_DOWNLOAD_TOKEN"
