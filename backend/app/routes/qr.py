import io
import qrcode
from fastapi import APIRouter, Response
from ..config import BASE_URL

router = APIRouter(tags=["qr"])


@router.get("/qr/{token}")
def generate_qr(token: str):
    """Generate QR code for a result link."""
    url = f"{BASE_URL}/r/{token}"

    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    return Response(content=buf.getvalue(), media_type="image/png")
