import base64
import binascii
from html import escape
from io import BytesIO

import qrcode
from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError
from qrcode.exceptions import DataOverflowError

from app.core.exceptions import ApplicationError
from app.models.qr_generation import QrDesign, QrFileFormat


ERROR_CORRECTION = {
    "L": qrcode.constants.ERROR_CORRECT_L,
    "M": qrcode.constants.ERROR_CORRECT_M,
    "Q": qrcode.constants.ERROR_CORRECT_Q,
    "H": qrcode.constants.ERROR_CORRECT_H,
}


class QrRenderer:
    def render_all(
        self,
        payload: str,
        design: QrDesign | None = None,
        logo: bytes | None = None,
    ) -> dict[QrFileFormat, bytes]:
        selected = design or QrDesign()
        try:
            matrix = self._matrix(payload, selected.error_correction)
            png = self._render_png(matrix, selected, logo)
            return {
                "png": png,
                "svg": self._render_svg(matrix, selected, logo),
                "pdf": self._render_pdf(png),
            }
        except DataOverflowError as exc:
            raise ApplicationError("QR payload is too large") from exc

    @staticmethod
    def normalize_logo(data_url: str | None) -> bytes | None:
        if not data_url:
            return None
        try:
            header, encoded = data_url.split(",", 1)
            if header.lower() not in {"data:image/png;base64", "data:image/jpeg;base64"}:
                raise ApplicationError("Logo must be a PNG or JPEG image")
            raw = base64.b64decode(encoded, validate=True)
        except (ValueError, binascii.Error) as exc:
            raise ApplicationError("Logo data is invalid") from exc
        if len(raw) > 2 * 1024 * 1024:
            raise ApplicationError("Logo must be no larger than 2 MB")
        try:
            with Image.open(BytesIO(raw)) as source:
                source.load()
                if source.format not in {"PNG", "JPEG"}:
                    raise ApplicationError("Logo must be a PNG or JPEG image")
                if source.width > 2048 or source.height > 2048 or source.width * source.height > 4_000_000:
                    raise ApplicationError("Logo dimensions are too large")
                image = source.convert("RGBA")
                image.thumbnail((512, 512), Image.Resampling.LANCZOS)
                output = BytesIO()
                image.save(output, format="PNG", optimize=True)
                return output.getvalue()
        except (UnidentifiedImageError, OSError) as exc:
            raise ApplicationError("Logo image could not be decoded") from exc

    @staticmethod
    def _matrix(payload: str, correction: str) -> list[list[bool]]:
        qr = qrcode.QRCode(
            version=None,
            error_correction=ERROR_CORRECTION[correction],
            box_size=1,
            border=0,
        )
        qr.add_data(payload)
        qr.make(fit=True)
        return qr.get_matrix()

    def _render_png(self, matrix: list[list[bool]], design: QrDesign, logo: bytes | None) -> bytes:
        size = design.size
        image = Image.new("RGBA", (size, size), design.background_color)
        draw = ImageDraw.Draw(image)
        left, top, module_size, qr_size, text_height = self._layout(len(matrix), design)
        self._draw_frame(draw, design, size, text_height)

        for row, values in enumerate(matrix):
            for column, enabled in enumerate(values):
                if not enabled:
                    continue
                color = self._module_color(row, column, len(matrix), design)
                x0 = left + (design.margin + column) * module_size
                y0 = top + (design.margin + row) * module_size
                x1 = x0 + module_size
                y1 = y0 + module_size
                finder = self._is_finder(row, column, len(matrix))
                if design.module_style == "dots" and not finder:
                    inset = max(1, module_size // 10)
                    draw.ellipse((x0 + inset, y0 + inset, x1 - inset, y1 - inset), fill=color)
                elif design.module_style == "rounded" and not finder:
                    draw.rounded_rectangle((x0, y0, x1, y1), radius=max(1, module_size // 3), fill=color)
                else:
                    draw.rectangle((x0, y0, x1, y1), fill=color)

        if logo:
            self._paste_logo(image, logo, left, top, qr_size, design.background_color)
        output = BytesIO()
        image.convert("RGB").save(output, format="PNG", optimize=True)
        return output.getvalue()

    def _render_svg(self, matrix: list[list[bool]], design: QrDesign, logo: bytes | None) -> bytes:
        size = design.size
        left, top, module_size, qr_size, text_height = self._layout(len(matrix), design)
        elements = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 {size} {size}">',
            f'<rect width="{size}" height="{size}" fill="{design.background_color}"/>',
        ]
        if design.frame_style != "none":
            inset = max(4, size // 80)
            radius = size // 28 if design.frame_style == "rounded" else 0
            elements.append(
                f'<rect x="{inset}" y="{inset}" width="{size - inset * 2}" height="{size - inset * 2}" rx="{radius}" fill="none" stroke="{design.foreground_color}" stroke-width="{max(3, size // 100)}"/>'
            )
        for row, values in enumerate(matrix):
            for column, enabled in enumerate(values):
                if not enabled:
                    continue
                color = self._module_color(row, column, len(matrix), design)
                x = left + (design.margin + column) * module_size
                y = top + (design.margin + row) * module_size
                finder = self._is_finder(row, column, len(matrix))
                if design.module_style == "dots" and not finder:
                    radius = module_size * 0.42
                    elements.append(f'<circle cx="{x + module_size / 2:.2f}" cy="{y + module_size / 2:.2f}" r="{radius:.2f}" fill="{color}"/>')
                else:
                    radius = module_size * 0.3 if design.module_style == "rounded" and not finder else 0
                    elements.append(f'<rect x="{x}" y="{y}" width="{module_size}" height="{module_size}" rx="{radius:.2f}" fill="{color}"/>')
        if logo:
            logo_size = max(24, int(qr_size * 0.18))
            x = left + (qr_size - logo_size) / 2
            y = top + (qr_size - logo_size) / 2
            padding = max(4, int(logo_size * 0.12))
            elements.append(f'<rect x="{x - padding:.2f}" y="{y - padding:.2f}" width="{logo_size + padding * 2:.2f}" height="{logo_size + padding * 2:.2f}" rx="{padding * 1.5:.2f}" fill="{design.background_color}"/>')
            encoded = base64.b64encode(logo).decode("ascii")
            elements.append(f'<image href="data:image/png;base64,{encoded}" x="{x:.2f}" y="{y:.2f}" width="{logo_size}" height="{logo_size}" preserveAspectRatio="xMidYMid meet"/>')
        if design.frame_style != "none" and design.frame_text:
            font_size = max(12, size // 28)
            y = size - max(12, text_height // 3)
            elements.append(f'<text x="{size / 2}" y="{y}" text-anchor="middle" font-family="Arial,sans-serif" font-size="{font_size}" font-weight="600" fill="{design.foreground_color}">{escape(design.frame_text)}</text>')
        elements.append("</svg>")
        return "".join(elements).encode("utf-8")

    @staticmethod
    def _render_pdf(png: bytes) -> bytes:
        output = BytesIO()
        with Image.open(BytesIO(png)) as image:
            image.convert("RGB").save(output, format="PDF", resolution=300.0)
        return output.getvalue()

    @staticmethod
    def _layout(matrix_size: int, design: QrDesign) -> tuple[int, int, int, int, int]:
        size = design.size
        frame_inset = size // 28 if design.frame_style != "none" else 0
        text_height = size // 12 if design.frame_style != "none" and design.frame_text else 0
        available_width = size - frame_inset * 2
        available_height = size - frame_inset * 2 - text_height
        modules = matrix_size + design.margin * 2
        module_size = max(1, min(available_width, available_height) // modules)
        qr_size = modules * module_size
        left = (size - qr_size) // 2
        top = frame_inset + max(0, (available_height - qr_size) // 2)
        return left, top, module_size, qr_size, text_height

    @staticmethod
    def _module_color(row: int, column: int, matrix_size: int, design: QrDesign) -> str:
        if not design.gradient_enabled:
            return design.foreground_color
        denominator = max(1, matrix_size - 1)
        if design.gradient_direction == "horizontal":
            amount = column / denominator
        elif design.gradient_direction == "vertical":
            amount = row / denominator
        else:
            amount = (row + column) / (denominator * 2)
        start = tuple(int(design.foreground_color[index:index + 2], 16) for index in (1, 3, 5))
        end = tuple(int(design.gradient_color[index:index + 2], 16) for index in (1, 3, 5))
        channels = tuple(round(a + (b - a) * amount) for a, b in zip(start, end))
        return "#{:02X}{:02X}{:02X}".format(*channels)

    @staticmethod
    def _is_finder(row: int, column: int, size: int) -> bool:
        return (row < 7 and column < 7) or (row < 7 and column >= size - 7) or (row >= size - 7 and column < 7)

    @staticmethod
    def _paste_logo(image: Image.Image, logo: bytes, left: int, top: int, qr_size: int, background: str) -> None:
        with Image.open(BytesIO(logo)) as source:
            mark = source.convert("RGBA")
            maximum = max(24, int(qr_size * 0.18))
            mark.thumbnail((maximum, maximum), Image.Resampling.LANCZOS)
            x = left + (qr_size - mark.width) // 2
            y = top + (qr_size - mark.height) // 2
            padding = max(4, int(max(mark.size) * 0.12))
            plate = Image.new("RGBA", (mark.width + padding * 2, mark.height + padding * 2), (0, 0, 0, 0))
            plate_draw = ImageDraw.Draw(plate)
            plate_draw.rounded_rectangle(plate.getbbox() or (0, 0, plate.width, plate.height), radius=padding * 2, fill=background)
            plate.alpha_composite(mark, (padding, padding))
            image.alpha_composite(plate, (x - padding, y - padding))

    @staticmethod
    def _draw_frame(draw: ImageDraw.ImageDraw, design: QrDesign, size: int, text_height: int) -> None:
        if design.frame_style == "none":
            return
        inset = max(4, size // 80)
        width = max(3, size // 100)
        box = (inset, inset, size - inset, size - inset)
        if design.frame_style == "rounded":
            draw.rounded_rectangle(box, radius=size // 28, outline=design.foreground_color, width=width)
        else:
            draw.rectangle(box, outline=design.foreground_color, width=width)
        if design.frame_text:
            try:
                font = ImageFont.truetype("DejaVuSans-Bold.ttf", max(12, size // 28))
            except OSError:
                font = ImageFont.load_default()
            y = size - max(12, text_height // 2)
            draw.text((size // 2, y), design.frame_text, fill=design.foreground_color, font=font, anchor="mm")
