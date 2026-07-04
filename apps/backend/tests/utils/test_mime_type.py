from app.utils import resolve_mime_type


def test_resolve_mime_type_from_xlsx_extension():
    assert (
        resolve_mime_type("report.xlsx", "text/plain")
        == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


def test_resolve_mime_type_keeps_explicit_type():
    assert (
        resolve_mime_type("report.xlsx", "application/custom") == "application/custom"
    )


def test_resolve_mime_type_fallback_octet_stream():
    assert resolve_mime_type("data.bin", None) == "application/octet-stream"
