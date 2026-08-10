from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from src.catalog.constants import (
    IMAGE_SIGNATURES,
    MAX_UPLOAD_BYTES,
    MEDIA_URL_PREFIX,
    UPLOAD_CHUNK_BYTES,
)
from src.catalog.exceptions import ImageTooLarge, UnreadableImage
from src.config import settings


def extension_for(head: bytes) -> str | None:
    for magic, extra, suffix in IMAGE_SIGNATURES:
        if not head.startswith(magic):
            continue
        if all(head[at : at + len(marker)] == marker for at, marker in extra):
            return suffix
    return None


async def store(upload: UploadFile) -> str:
    head = await upload.read(UPLOAD_CHUNK_BYTES)
    suffix = extension_for(head)
    if suffix is None:
        raise UnreadableImage()

    directory = settings.media_dir
    directory.mkdir(parents=True, exist_ok=True)
    name = f"{uuid4().hex}{suffix}"
    written = 0
    target = directory / name

    try:
        with target.open("wb") as sink:
            while head:
                written += len(head)
                if written > MAX_UPLOAD_BYTES:
                    raise ImageTooLarge()
                sink.write(head)
                head = await upload.read(UPLOAD_CHUNK_BYTES)
    except BaseException:
        Path(target).unlink(missing_ok=True)
        raise

    return f"{MEDIA_URL_PREFIX}/{name}"
