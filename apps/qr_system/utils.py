import io
import qrcode
from django.core.files.base import ContentFile


def generate_qr_for_booking(booking) -> None:
    payload = f"OnePass|{booking.pnr}|{booking.qr_token}"
    img = qrcode.make(payload)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    booking.qr_image.save(f"{booking.pnr}.png", ContentFile(buf.getvalue()), save=False)
