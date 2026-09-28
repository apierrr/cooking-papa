"""Recompresse les photos uploadées avant la normalisation automatique.

Chaque image référencée en base est passée dans le même pipeline que les
nouveaux uploads (crop carré centré, max 1024px, JPEG). Les images déjà
normalisées (JPEG carré <= 1024px) sont laissées telles quelles.

Usage (depuis la racine du projet, conteneur en marche) :
    docker exec -i cooking-papa python - --dry-run < scripts/recompress_images.py
    docker exec -i cooking-papa python -           < scripts/recompress_images.py
    docker exec -i cooking-papa python - --force   < scripts/recompress_images.py
--force retraite aussi les images déjà normalisées (utile pour retirer
des métadonnées d'images passées par une ancienne version du pipeline).
"""
import sys
from pathlib import Path

from PIL import Image
from sqlalchemy import select

from app.config import UPLOAD_DIR, IMAGE_SIZE
from app.db import SessionLocal
from app.models import Recipe
from app.uploads import _normalize

dry_run = "--dry-run" in sys.argv
force = "--force" in sys.argv


def already_normalized(path: Path) -> bool:
    with Image.open(path) as img:
        w, h = img.size
        return img.format == "JPEG" and w == h and w <= IMAGE_SIZE


def main() -> None:
    db = SessionLocal()
    referenced: set[str] = set()
    try:
        recipes = db.scalars(select(Recipe).where(Recipe.image_path.is_not(None))).all()
        for recipe in recipes:
            referenced.add(recipe.image_path)
            src = UPLOAD_DIR / recipe.image_path
            if not src.is_file():
                print(f"[MANQUANT] recette {recipe.id} « {recipe.title} » : {recipe.image_path}")
                continue
            if already_normalized(src) and not force:
                print(f"[OK]       recette {recipe.id} « {recipe.title} » : {src.name} déjà normalisée")
                continue

            old_size = src.stat().st_size
            data = _normalize(src.read_bytes())
            dest = src.with_suffix(".jpg")
            print(f"[CONVERTI] recette {recipe.id} « {recipe.title} » : "
                  f"{src.name} ({old_size // 1024} Ko) -> {dest.name} ({len(data) // 1024} Ko)"
                  + (" [dry-run]" if dry_run else ""))
            if dry_run:
                continue

            dest.write_bytes(data)
            recipe.image_path = dest.name
            db.commit()
            referenced.add(dest.name)
            if src != dest:
                src.unlink(missing_ok=True)

        for orphan in sorted(p.name for p in UPLOAD_DIR.iterdir()
                             if p.is_file() and p.name not in referenced):
            print(f"[ORPHELIN] {orphan} : présent sur le disque mais référencé par aucune recette")
    finally:
        db.close()


if __name__ == "__main__":
    main()
