import os
from pathlib import Path

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:////app/data/cooking.db")
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "/app/uploads"))
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "20"))
MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024

# Uploaded photos are normalized: center-cropped square, at most IMAGE_SIZE px, JPEG.
IMAGE_SIZE = int(os.getenv("IMAGE_SIZE", "1024"))
IMAGE_JPEG_QUALITY = int(os.getenv("IMAGE_JPEG_QUALITY", "85"))

CSRF_SECRET = os.environ["CSRF_SECRET"]

DISCORD_ENABLED = os.getenv("DISCORD_ENABLED", "false").lower() == "true"
DISCORD_HOST = os.getenv("DISCORD_HOST", "")
DISCORD_TARGET_USER = os.getenv("DISCORD_TARGET_USER", "")

ALLOWED_IMAGE_MIMES = {"image/jpeg", "image/png", "image/webp", "image/gif"}

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
