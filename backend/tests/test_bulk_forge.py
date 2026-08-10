from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

from openpyxl import Workbook

from app.infrastructure.bulk.parser import BulkImportParser
from app.infrastructure.bulk.zip_storage import BulkZipStorage


def test_csv_parser_validates_multiple_qr_types_and_isolates_bad_rows() -> None:
    content = (
        "type,label,url,text,phone\n"
        "url,Website,https://example.com,,\n"
        "text,Note,,Hello IntelliQR,\n"
        "phone,Bad phone,,,+not-valid\n"
    ).encode()

    requests, errors, total = BulkImportParser(250).parse("batch.csv", content)

    assert total == 3
    assert [request.type for _, request in requests] == ["url", "text"]
    assert errors[0]["row"] == 4


def test_xlsx_parser_reads_spreadsheet_rows() -> None:
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["type", "label", "email", "subject"])
    sheet.append(["email", "Support", "help@example.com", "Hello"])
    output = BytesIO()
    workbook.save(output)

    requests, errors, total = BulkImportParser(250).parse("batch.xlsx", output.getvalue())

    assert total == 1
    assert not errors
    assert requests[0][1].type == "email"


def test_zip_storage_packages_requested_files_with_safe_names(tmp_path: Path) -> None:
    png = tmp_path / "source.png"
    svg = tmp_path / "source.svg"
    png.write_bytes(b"png")
    svg.write_bytes(b"svg")
    storage = BulkZipStorage(tmp_path / "archives")

    relative = storage.create("job-id", [(png, "1 Product / QR.png"), (svg, "1 Product / QR.svg")])

    with ZipFile(storage.resolve(relative)) as archive:
        assert archive.namelist() == ["1-Product-QR.png", "1-Product-QR.svg"]
