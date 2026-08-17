from app.routes import id_scan

from tests.conftest import auth_headers


def test_national_id_ocr_is_disabled_without_explicit_government_provider(
    client, make_lab, make_lab_user, monkeypatch
):
    lab = make_lab("Synthetic Identity Guard Lab")
    user = make_lab_user(lab.id, role="admin")
    monkeypatch.setattr(id_scan, "ENABLE_NATIONAL_ID_OCR", False)
    monkeypatch.setattr(id_scan, "GOVERNMENT_IDENTITY_PROVIDER", "UNVERIFIED")

    response = client.post(
        "/id-scan/scan",
        headers=auth_headers(user.id, lab.id, "admin"),
        files={"image": ("synthetic.png", b"not-an-image", "image/png")},
    )

    assert response.status_code == 503
    assert "national" not in response.text.lower()
    assert "unexpected error" in response.json()["detail"].lower()
