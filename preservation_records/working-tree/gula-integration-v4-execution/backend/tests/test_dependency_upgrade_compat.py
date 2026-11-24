"""Phase-1 dependency upgrade compatibility tests (DEP-AUDIT-BACKEND).

Context
-------
``pip-audit`` reported 55 known advisories across 6 runtime libraries
(pillow, joserfc, certifi, dnspython, pyasn1, urllib3). All six were raised to
their **minimum fix version** in ``requirements.txt`` / ``requirements-lock.txt``
/ ``pyproject.toml``.

These tests prove **functional non-regression** of the code paths those
libraries serve. They are deliberately **behaviour-only**:

* no ``__version__`` / pin assertions — a version assertion would test the
  manifest, not the behaviour, and would fail in any environment that
  legitimately resolves a newer compatible build;
* every assertion is about *output* (bytes, headers, decoded claims, parsed
  names), so the same file passes on the pre-upgrade baseline and on the
  remediated set. The upgrade's correctness is demonstrated by running this
  file under both dependency sets, not by hard-coding a version.

Covered runtime paths
---------------------
====================  =============================================
Library               Production path exercised here
====================  =============================================
pillow                ``routes/id_scan.py`` (``Image.open``),
                      ``integration/connectors/barcode.py``
qrcode -> pillow      ``shared/qr/generator.py::generate_qr_image``
reportlab + QR        ``shared/pdf/generator.py::generate_result_pdf``
joserfc               ``security/oauth2_provider.py`` (JWT sign/verify)
certifi               root CA bundle for all outbound TLS
urllib3               transport under ``requests`` / ``sentry-sdk``
dnspython             ``email-validator`` DNS name handling
email-validator       ``EmailStr`` validation on auth payloads
pyasn1                ASN.1 encode/decode under ``webauthn``
====================  =============================================
"""

from __future__ import annotations

import io

# PNG / PDF magic numbers
_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
_PDF_MAGIC = b"%PDF"


# --------------------------------------------------------------------------
# pillow — Image.open / save round-trip (id_scan.py, barcode.py pattern)
# --------------------------------------------------------------------------
class TestPillowImagePaths:
    def test_png_roundtrip_preserves_pixels(self):
        from PIL import Image

        src = Image.new("RGB", (32, 16), color=(10, 200, 30))
        buf = io.BytesIO()
        src.save(buf, format="PNG")

        raw = buf.getvalue()
        assert raw.startswith(_PNG_MAGIC), "save() must emit a real PNG"

        with Image.open(io.BytesIO(raw)) as img:
            assert img.size == (32, 16)
            assert img.mode == "RGB"
            # pixel fidelity through the encode/decode cycle
            assert img.getpixel((0, 0)) == (10, 200, 30)
            assert img.getpixel((31, 15)) == (10, 200, 30)

    def test_open_from_bytes_handles_jpeg(self):
        """Mirrors ``routes/id_scan.py``: ``Image.open(io.BytesIO(image_bytes))``."""
        from PIL import Image

        buf = io.BytesIO()
        Image.new("L", (64, 64), color=128).save(buf, format="JPEG")
        jpeg = buf.getvalue()
        assert jpeg[:2] == b"\xff\xd8", "expected a JPEG SOI marker"

        with Image.open(io.BytesIO(jpeg)) as img:
            assert img.size == (64, 64)
            # grayscale survives; JPEG is lossy so compare with tolerance
            pixel = img.convert("L").getpixel((32, 32))
            assert abs(pixel - 128) <= 3

    def test_image_frombytes_buffer_path(self):
        """Core buffer constructor used when raw frames are decoded."""
        from PIL import Image

        data = bytes(range(16)) * 3  # 16 pixels x 3 channels
        img = Image.frombytes("RGB", (4, 4), data)
        assert img.size == (4, 4)
        # row-major: pixel (x, y) starts at (y * width + x) * 3
        assert img.getpixel((0, 0)) == tuple(data[0:3])
        assert img.getpixel((3, 3)) == tuple(data[45:48])
        assert img.getpixel((3, 3)) == (13, 14, 15)

    def test_image_resample_and_thumbnail(self):
        """Downscaling path used by document-intelligence preprocessing."""
        from PIL import Image

        img = Image.new("RGB", (400, 400), color=(255, 0, 0))
        img.thumbnail((100, 100))
        assert img.size == (100, 100)


# --------------------------------------------------------------------------
# qrcode -> pillow (shared/qr/generator.py) — previously had no test coverage
# --------------------------------------------------------------------------
class TestQrImageGeneration:
    def test_generate_qr_image_emits_png(self):
        from shared.qr import generate_qr_image

        png = generate_qr_image("https://gula.example/r/abc123")
        assert isinstance(png, bytes)
        assert png.startswith(_PNG_MAGIC), "generate_qr_image must return PNG bytes"
        assert len(png) > 200, "QR PNG should not be trivially small"

    def test_generate_qr_image_is_openable_by_pillow(self):
        """The QR bytes are embedded into PDFs by reportlab — must be loadable."""
        from PIL import Image

        from shared.qr import generate_qr_image

        png = generate_qr_image("ORDER-2026-0001", box_size=4, border=2)
        with Image.open(io.BytesIO(png)) as img:
            assert img.format == "PNG"
            assert img.size[0] == img.size[1], "QR codes are square"
            assert img.size[0] > 20

    def test_generate_qr_matrix_is_non_empty(self):
        from shared.qr import generate_qr

        qr = generate_qr("https://gula.example/result/9")
        matrix = qr.modules
        assert len(matrix) > 0
        assert all(len(row) == len(matrix) for row in matrix), "matrix must be rectangular"

    def test_generate_qr_svg_is_markup(self):
        from shared.qr import generate_qr_svg

        svg = generate_qr_svg("https://gula.example/result/9")
        assert svg.lstrip().startswith("<svg"), "SVG generator must emit <svg>"

    def test_qr_output_is_deterministic(self):
        """Same input -> same bytes (stable encoding, no per-call randomness)."""
        from shared.qr import generate_qr_image

        a = generate_qr_image("DETERMINISTIC-INPUT")
        b = generate_qr_image("DETERMINISTIC-INPUT")
        assert a == b


# --------------------------------------------------------------------------
# reportlab + qrcode + pillow combined (shared/pdf/generator.py)
# --------------------------------------------------------------------------
class TestPdfWithQr:
    _DATA = {
        "patient_name": "Test Patient",
        "test_name": "Complete Blood Count",
        "result_value": "7.1",
        "reference_range": "4.0-11.0",
        "date": "2026-11-16",
    }

    def test_pdf_without_qr_has_pdf_header(self):
        from shared.pdf import generate_result_pdf

        pdf = generate_result_pdf(self._DATA, result_url="")
        assert isinstance(pdf, bytes)
        assert pdf.startswith(_PDF_MAGIC)
        assert len(pdf) > 500

    def test_pdf_with_qr_has_pdf_header(self):
        """Exercises the full qrcode -> pillow -> reportlab embedding branch
        (``if tpl.show_qr and result_url:`` in ``shared/pdf/generator.py``)."""
        from shared.pdf import generate_result_pdf

        pdf = generate_result_pdf(self._DATA, result_url="https://gula.example/r/xyz")
        assert pdf.startswith(_PDF_MAGIC)
        assert len(pdf) > 500
        assert b"%%EOF" in pdf[-1024:], "PDF must be properly terminated"

    def test_pdf_with_explicit_template_qr(self):
        from shared.pdf import PDFTemplate, generate_result_pdf

        tpl = PDFTemplate(title="نتيجة فحص", show_qr=True, language="ar")
        pdf = generate_result_pdf(self._DATA, result_url="https://gula.example/r/1", template=tpl)
        assert pdf.startswith(_PDF_MAGIC)

    def test_pdf_with_qr_disabled(self):
        from shared.pdf import PDFTemplate, generate_result_pdf

        tpl = PDFTemplate(show_qr=False)
        pdf = generate_result_pdf(self._DATA, result_url="https://gula.example/r/1", template=tpl)
        assert pdf.startswith(_PDF_MAGIC)


# --------------------------------------------------------------------------
# joserfc — JWT sign / verify (security/oauth2_provider.py pattern)
# --------------------------------------------------------------------------
class TestJoserfcJwt:
    def _key(self):
        from joserfc import jwk

        return jwk.generate_key("oct", 256)

    def test_sign_and_decode_roundtrip(self):
        from joserfc import jwt as jose_jwt

        key = self._key()
        token = jose_jwt.encode({"alg": "HS256"}, {"sub": "user-1", "scope": "lab:read"}, key)
        assert isinstance(token, str)
        assert token.count(".") == 2, "compact JWS must be header.payload.signature"

        decoded = jose_jwt.decode(token, key)
        assert decoded.claims["sub"] == "user-1"
        assert decoded.claims["scope"] == "lab:read"
        assert decoded.header["alg"] == "HS256"

    def test_tampered_token_is_rejected(self):
        """Authorization must not accept a modified token — the core security
        property the joserfc DoS fixes must not have disturbed."""
        import base64

        from joserfc import jwt as jose_jwt

        key = self._key()
        token = jose_jwt.encode({"alg": "HS256"}, {"sub": "user-1"}, key)

        header, _payload, sig = token.split(".")

        def _b64(obj: dict) -> str:
            raw = __import__("json").dumps(obj, separators=(",", ":")).encode()
            return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()

        # escalate privileges in the payload, keep the original signature
        forged = f"{header}.{_b64({'sub': 'admin', 'alg': 'HS256'})}.{sig}"

        try:
            jose_jwt.decode(forged, key)
        except Exception:
            return  # correctly rejected
        raise AssertionError("forged JWT must not verify")

    def test_wrong_key_is_rejected(self):
        from joserfc import jwt as jose_jwt

        token = jose_jwt.encode({"alg": "HS256"}, {"sub": "user-1"}, self._key())
        try:
            jose_jwt.decode(token, self._key())
        except Exception:
            return
        raise AssertionError("token signed with a different key must not verify")

    def test_essential_claim_validation(self):
        from joserfc import jwt as jose_jwt
        from joserfc.errors import MissingClaimError

        key = self._key()
        token = jose_jwt.encode({"alg": "HS256"}, {"sub": "u"}, key)
        claims = jose_jwt.decode(token, key).claims

        # NOTE: claims options are **keyword** arguments to JWTClaimsRegistry
        # (signature is ``__init__(now=None, leeway=0, **kwargs)``) — a
        # positional dict would be bound to ``now`` and silently disable
        # essential-claim checking.
        registry = jose_jwt.JWTClaimsRegistry(sub={"essential": True})
        assert registry.validate(claims) is None  # type: ignore[func-returns-value]

        # missing essential claim must be reported, not silently accepted
        try:
            jose_jwt.JWTClaimsRegistry(role={"essential": True}).validate(claims)
        except MissingClaimError:
            return
        raise AssertionError("missing essential claim must raise MissingClaimError")

    def test_jwk_generation(self):
        from joserfc import jwk

        key = jwk.generate_key("oct", 256)
        assert key is not None
        assert key.key_type == "oct"


# --------------------------------------------------------------------------
# certifi — outbound TLS trust bundle
# --------------------------------------------------------------------------
class TestCertifiBundle:
    def test_bundle_path_exists_and_is_non_empty(self):
        import os

        import certifi

        path = certifi.where()
        assert os.path.isfile(path), "CA bundle path must point at a real file"
        assert os.path.getsize(path) > 10_000, "CA bundle must contain root CAs"

    def test_bundle_parses_as_pem(self):
        import certifi

        with open(certifi.where(), "rb") as fh:
            data = fh.read()
        assert b"BEGIN CERTIFICATE" in data
        # the advisory was about compromised bundled roots; the refreshed
        # bundle must still be a well-formed PEM collection
        assert data.count(b"BEGIN CERTIFICATE") == data.count(b"END CERTIFICATE")


# --------------------------------------------------------------------------
# urllib3 — HTTP transport (via requests / sentry-sdk)
# --------------------------------------------------------------------------
class TestUrllib3Transport:
    def test_core_api_available(self):
        from urllib3 import PoolManager
        from urllib3.util import Retry, Timeout

        assert PoolManager is not None
        assert Retry is not None
        assert Timeout is not None

    def test_retry_configuration_roundtrip(self):
        from urllib3.util import Retry

        r = Retry(total=3, backoff_factor=0.5, status_forcelist=(502, 503, 504))
        assert r.total == 3
        assert r.backoff_factor == 0.5

    def test_https_url_parse(self):
        from urllib3.util import parse_url

        p = parse_url("https://api.gula.example/v1/patients?limit=10")
        assert p.scheme == "https"
        assert p.host == "api.gula.example"
        assert p.path == "/v1/patients"


# --------------------------------------------------------------------------
# dnspython — DNS name parsing (email-validator path)
# --------------------------------------------------------------------------
class TestDnspythonNames:
    def test_from_text_roundtrip(self):
        import dns.name

        n = dns.name.from_text("gula.example.")
        assert n.to_text() == "gula.example."
        assert len(n.labels) >= 2

    def test_absolute_name(self):
        import dns.name

        n = dns.name.from_text("labs.health.gov.iq.")
        assert n.is_absolute()
        assert n.to_text().endswith(".")

    def test_name_from_wire(self):
        """Exercises the wire parser implicated in the CPU-exhaustion
        advisories — with a well-formed input it must simply parse."""
        import dns.name

        wire = dns.name.from_text("gula.example.").to_wire()
        parsed = dns.name.from_wire(wire, 0)
        assert parsed[0].to_text() == "gula.example."


# --------------------------------------------------------------------------
# email-validator — EmailStr validation on auth payloads
# --------------------------------------------------------------------------
class TestEmailValidation:
    def test_valid_email_is_accepted(self):
        from email_validator import validate_email

        result = validate_email("user@gula.example", check_deliverability=False)
        assert result.normalized == "user@gula.example"

    def test_invalid_email_is_rejected(self):
        from email_validator import EmailNotValidError, validate_email

        for bad in ("not-an-email", "a@b", "@no-local", "spaces in@example.com"):
            try:
                validate_email(bad, check_deliverability=False)
            except EmailNotValidError:
                continue
            raise AssertionError(f"{bad!r} must be rejected")

    def test_normalization(self):
        from email_validator import validate_email

        result = validate_email("Mixed.Case@Gula.Example", check_deliverability=False)
        assert result.normalized == "Mixed.Case@gula.example"

    def test_surrounding_whitespace_is_rejected(self):
        """Whitespace must be rejected outright rather than silently stripped —
        stripping would let a padded address bypass local-part validation."""
        from email_validator import EmailNotValidError, validate_email

        try:
            validate_email("  user@gula.example ", check_deliverability=False)
        except EmailNotValidError:
            return
        raise AssertionError("padded email address must be rejected")


# --------------------------------------------------------------------------
# pyasn1 — ASN.1 encode/decode (webauthn / FIDO2 path)
# --------------------------------------------------------------------------
class TestPyAsn1:
    def test_integer_roundtrip(self):
        from pyasn1.type import univ

        v = univ.Integer(42)
        assert int(v) == 42

    def test_octet_string_roundtrip(self):
        from pyasn1.codec.der import decoder, encoder
        from pyasn1.type import univ

        original = univ.OctetString(b"gula-platform")
        encoded = encoder.encode(original)
        assert isinstance(encoded, bytes)

        decoded, rest = decoder.decode(encoded)
        assert bytes(decoded) == b"gula-platform"
        assert rest == b""

    def test_sequence_roundtrip(self):
        from pyasn1.codec.der import decoder, encoder
        from pyasn1.type import namedtype, univ

        class Pair(univ.Sequence):
            componentType = namedtype.NamedTypes(
                namedtype.NamedType("id", univ.Integer()),
                namedtype.NamedType("label", univ.OctetString()),
            )

        obj = Pair()
        obj["id"] = 7
        obj["label"] = b"lab-01"

        decoded, _ = decoder.decode(encoder.encode(obj), asn1Spec=Pair())
        assert int(decoded["id"]) == 7
        assert bytes(decoded["label"]) == b"lab-01"
