from fastapi.routing import APIRoute
import mimetypes
from pathlib import PurePosixPath

# slim 镜像默认 mimetypes 库缺少 Office 等常见扩展名
_EXTRA_MIME_TYPES: dict[str, str] = {
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".xls": "application/vnd.ms-excel",
    ".xlsm": "application/vnd.ms-excel.sheet.macroEnabled.12",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".doc": "application/msword",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ".ppt": "application/vnd.ms-powerpoint",
    ".csv": "text/csv",
    ".pdf": "application/pdf",
    ".zip": "application/zip",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
}

for _ext, _mime in _EXTRA_MIME_TYPES.items():
    mimetypes.add_type(_mime, _ext)

# multipart 上传常见「泛型」类型，应优先用文件名推断
_GENERIC_MIME_TYPES = frozenset(
    {
        "",
        "application/octet-stream",
        "binary/octet-stream",
        "text/plain",
    }
)


def _guess_mime_from_filename(filename: str) -> str | None:
    suffix = PurePosixPath(filename).suffix.lower()
    if suffix in _EXTRA_MIME_TYPES:
        return _EXTRA_MIME_TYPES[suffix]
    guessed, _ = mimetypes.guess_type(filename)
    return guessed


def resolve_mime_type(filename: str, content_type: str | None) -> str:
    """Prefer filename extension when multipart Content-Type is missing or generic."""
    normalized = (content_type or "").split(";", 1)[0].strip().lower()
    guessed = _guess_mime_from_filename(filename)

    if normalized in _GENERIC_MIME_TYPES:
        return guessed or normalized or "application/octet-stream"

    return content_type or guessed or "application/octet-stream"


def simple_generate_unique_route_id(route: APIRoute):
    return f"{route.tags[0]}-{route.name}"
