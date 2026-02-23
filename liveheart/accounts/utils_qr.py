import qrcode
from io import BytesIO
import base64


def generate_qr_code(uri: str) -> str:
    qr = qrcode.make(uri)
    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()
