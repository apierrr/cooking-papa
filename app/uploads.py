import io
import uuid
import magic
from fastapi import UploadFile, HTTPException, status
from PIL import Image, ImageCms, ImageOps, UnidentifiedImageError

from .config import UPLOAD_DIR, MAX_UPLOAD_BYTES, ALLOWED_IMAGE_MIMES, IMAGE_SIZE, IMAGE_JPEG_QUALITY

_SRGB = ImageCms.createProfile("sRGB")


def _normalize(data: bytes) -> bytes:
    """Center-crop to a square capped at IMAGE_SIZE px and re-encode as JPEG.

    The output carries no metadata: EXIF (incl. GPS), XMP, comments and ICC
    profile are dropped; colors are converted to sRGB first when a profile
    is present so wide-gamut photos (e.g. iPhone Display P3) stay accurate.
    """
    try:
        img = Image.open(io.BytesIO(data))
        icc = img.info.get("icc_profile")
        img = ImageOps.exif_transpose(img)
        side = min(IMAGE_SIZE, *img.size)
        img = ImageOps.fit(img, (side, side), method=Image.Resampling.LANCZOS)
        if img.mode in ("RGBA", "LA", "P", "PA"):
            img = img.convert("RGBA")
            flat = Image.new("RGB", img.size, (255, 255, 255))
            flat.paste(img, mask=img.getchannel("A"))
            img = flat
        elif img.mode != "RGB":
            img = img.convert("RGB")
        if icc:
            try:
                src_profile = ImageCms.ImageCmsProfile(io.BytesIO(icc))
                img = ImageCms.profileToProfile(img, src_profile, _SRGB, outputMode="RGB")
            except ImageCms.PyCMSError:
                pass  # unreadable/mismatched profile: keep pixels as-is
        img.info.clear()
        out = io.BytesIO()
        img.save(out, format="JPEG", quality=IMAGE_JPEG_QUALITY, optimize=True, exif=b"")
        return out.getvalue()
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError, ValueError):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid image file")


async def save_image(file: UploadFile) -> str:
    data = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "Image too large")
    if len(data) == 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Empty file")

    mime = magic.from_buffer(data, mime=True)
    if mime not in ALLOWED_IMAGE_MIMES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Unsupported image type: {mime}")

    name = f"{uuid.uuid4().hex}.jpg"
    dest = UPLOAD_DIR / name
    dest.write_bytes(_normalize(data))
    return name


def delete_image(name: str | None) -> None:
    """Remove a previously saved upload; ignores anything that isn't a bare filename."""
    if not name or "/" in name or "\\" in name or name.startswith("."):
        return
    (UPLOAD_DIR / name).unlink(missing_ok=True)
