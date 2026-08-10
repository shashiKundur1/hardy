from fastapi import HTTPException, status

from src.catalog.constants import MAX_UPLOAD_BYTES


class UnreadableImage(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            "That file is not a PNG, JPEG or WebP image",
        )


class ImageTooLarge(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            status.HTTP_413_CONTENT_TOO_LARGE,
            f"Images must be under {MAX_UPLOAD_BYTES // (1024 * 1024)}MB",
        )
