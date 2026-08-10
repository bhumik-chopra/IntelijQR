from io import BytesIO

import cv2
import numpy as np
from PIL import Image, UnidentifiedImageError

from app.core.exceptions import ApplicationError


class QrDecodeError(ApplicationError):
    status_code = 422
    code = "qr_not_detected"


class InvalidScanImageError(ApplicationError):
    status_code = 415
    code = "invalid_scan_image"


class QrImageDecoder:
    max_pixels = 25_000_000

    def decode(self, image_bytes: bytes) -> list[str]:
        try:
            with Image.open(BytesIO(image_bytes)) as image:
                if image.width * image.height > self.max_pixels:
                    raise InvalidScanImageError("Image dimensions are too large")
                image.verify()
        except InvalidScanImageError:
            raise
        except (UnidentifiedImageError, OSError) as exc:
            raise InvalidScanImageError("Upload a valid PNG, JPEG, or WebP image") from exc

        encoded = np.frombuffer(image_bytes, dtype=np.uint8)
        image = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
        if image is None:
            raise InvalidScanImageError("The uploaded image could not be read")

        detector = cv2.QRCodeDetector()
        decoded: list[str] = []
        try:
            found, values, _, _ = detector.detectAndDecodeMulti(image)
            if found:
                decoded.extend(value for value in values if value)
        except cv2.error:
            pass
        if not decoded:
            value, _, _ = detector.detectAndDecode(image)
            if value:
                decoded.append(value)
        if not decoded:
            try:
                from pyzbar.pyzbar import decode as zbar_decode
                decoded.extend(item.data.decode("utf-8", errors="replace") for item in zbar_decode(image))
            except (ImportError, OSError):
                pass
        unique = list(dict.fromkeys(item.strip() for item in decoded if item.strip()))
        if not unique:
            raise QrDecodeError("No readable QR code was found in this image")
        return unique[:10]
