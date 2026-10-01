"""
Secure File Storage Service
===========================
Handles image validation, sanitization, thumbnail generation, and secure file saving.
Never trusts browser-supplied file names or MIME types.
"""

import io
import uuid
from pathlib import Path
from typing import Tuple, Optional
from PIL import Image
from fastapi import HTTPException, UploadFile, status
from app.config import settings

ALLOWED_MAGIC_BYTES = {
    b"\xff\xd8\xff": "image/jpeg",
    b"\x89PNG\r\n\x1a\n": "image/png",
    b"RIFF": "image/webp"
}


class StorageService:
    def __init__(self, upload_dir: str = settings.LOCAL_UPLOAD_DIR):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.thumbnails_dir = self.upload_dir / "thumbnails"
        self.thumbnails_dir.mkdir(parents=True, exist_ok=True)
        self.heatmaps_dir = self.upload_dir / "heatmaps"
        self.heatmaps_dir.mkdir(parents=True, exist_ok=True)

    async def validate_and_save_upload(self, file: UploadFile) -> Tuple[str, str, Image.Image]:
        """
        Validates untrusted image upload:
        - Maximum size check
        - Magic bytes check
        - Image decoding verification
        - Returns (image_rel_url, thumbnail_rel_url, PIL Image object)
        """
        # Read file contents
        contents = await file.read()

        # 1. Size Validation
        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if len(contents) > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Image size exceeds maximum limit of {settings.MAX_UPLOAD_SIZE_MB}MB"
            )
        if len(contents) < 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty or corrupted."
            )

        # 2. Magic Bytes Validation
        is_valid_magic = False
        for magic in ALLOWED_MAGIC_BYTES:
            if contents.startswith(magic) or (magic == b"RIFF" and contents[8:12] == b"WEBP"):
                is_valid_magic = True
                break

        if not is_valid_magic:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="Invalid image format. Supported formats are JPEG, PNG, and WebP."
            )

        # 3. Pillow Decoding & Verification
        try:
            image_stream = io.BytesIO(contents)
            with Image.open(image_stream) as img:
                img.verify()

            # Reopen stream to load actual pixels
            image_stream.seek(0)
            pil_image = Image.open(image_stream).convert("RGB")
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is not a valid or readable image."
            )

        # 4. Generate Safe UUID Filename
        file_id = str(uuid.uuid4())
        filename = f"{file_id}.jpg"
        thumb_filename = f"{file_id}_thumb.jpg"

        dest_path = self.upload_dir / filename
        thumb_path = self.thumbnails_dir / thumb_filename

        # Save main image (normalized JPEG)
        pil_image.save(dest_path, "JPEG", quality=88, optimize=True)

        # Create & save thumbnail
        thumbnail = pil_image.copy()
        thumbnail.thumbnail((320, 240), Image.Resampling.LANCZOS)
        thumbnail.save(thumb_path, "JPEG", quality=80)

        image_url = f"/uploads/potholes/{filename}"
        thumb_url = f"/uploads/potholes/thumbnails/{thumb_filename}"

        return image_url, thumb_url, pil_image

    def save_heatmap_overlay(self, heatmap_image: Image.Image, file_id: str) -> str:
        """Saves Grad-CAM blended overlay image."""
        heatmap_filename = f"{file_id}_heatmap.jpg"
        dest_path = self.heatmaps_dir / heatmap_filename
        heatmap_image.save(dest_path, "JPEG", quality=85)
        return f"/uploads/potholes/heatmaps/{heatmap_filename}"


storage_service = StorageService()
