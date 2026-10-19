import os
import hashlib
from pathlib import Path
from fastapi import UploadFile, HTTPException
from app.config import settings
from app.observability.logger import logger

ALLOWED_MIME_TYPES = {
    "application/pdf": ".pdf",
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/tiff": ".tiff",
}

class StorageManager:
    def __init__(self):
        self.storage_dir = Path(settings.LOCAL_STORAGE_DIR)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    async def validate_and_save(self, file: UploadFile, workspace_id: str) -> dict:
        content_type = file.content_type or ""
        if content_type not in ALLOWED_MIME_TYPES:
            # Check filename extension fallback
            ext = Path(file.filename or "").suffix.lower()
            matching = [mime for mime, e in ALLOWED_MIME_TYPES.items() if e == ext]
            if matching:
                content_type = matching[0]
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported file type '{content_type}'. Allowed: PDF, PNG, JPG, TIFF."
                )

        # Read content to memory or chunk for validation
        content = await file.read()
        file_size = len(content)

        max_size_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if file_size > max_size_bytes:
            raise HTTPException(
                status_code=400,
                detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB}MB."
            )

        if file_size == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")

        # PDF header magic byte check
        if content_type == "application/pdf" and not content.startswith(b"%PDF"):
            raise HTTPException(status_code=400, detail="Invalid PDF file structure.")

        # Compute SHA256
        sha256 = hashlib.sha256(content).hexdigest()

        # Workspace directory isolation
        ws_dir = self.storage_dir / workspace_id
        ws_dir.mkdir(parents=True, exist_ok=True)

        ext = ALLOWED_MIME_TYPES.get(content_type, ".pdf")
        filename_on_disk = f"{sha256}{ext}"
        target_path = ws_dir / filename_on_disk

        with open(target_path, "wb") as f:
            f.write(content)

        logger.info(f"File stored: {target_path} (size={file_size} bytes, sha256={sha256})")

        return {
            "storage_path": str(target_path.resolve()),
            "checksum": sha256,
            "file_size_bytes": file_size,
            "mime_type": content_type,
            "original_filename": file.filename or "document.pdf",
        }

    def delete_file(self, storage_path: str):
        try:
            p = Path(storage_path)
            if p.exists():
                p.unlink()
                logger.info(f"File removed from storage: {storage_path}")
        except Exception as e:
            logger.error(f"Failed to delete file {storage_path}: {e}")

    def get_file_bytes(self, storage_path: str) -> bytes:
        p = Path(storage_path)
        if not p.exists():
            raise FileNotFoundError(f"File not found: {storage_path}")
        with open(p, "rb") as f:
            return f.read()

storage_manager = StorageManager()
