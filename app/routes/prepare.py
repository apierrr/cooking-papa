from fastapi import APIRouter, Depends, Request, Form, HTTPException, status
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Recipe, PreparationRequest
from ..security import verify_csrf
from ..discord import send_preparation_request
from ..templates import templates

router = APIRouter()


@router.post("/recipes/{recipe_id}/prepare")
async def prepare_recipe(
    recipe_id: int,
    request: Request,
    csrf_token: str = Form(...),
    note: str = Form("", max_length=500),
    db: Session = Depends(get_db),
):
    verify_csrf(request, csrf_token)

    recipe = db.get(Recipe, recipe_id)
    if not recipe:
        raise HTTPException(status.HTTP_404_NOT_FOUND)

    pr = PreparationRequest(recipe_id=recipe.id, note=note.strip() or None)
    db.add(pr)
    db.commit()
    db.refresh(pr)

    ingredient_lines = [
        f"{ri.quantity + ' ' if ri.quantity else ''}{ri.ingredient.name}"
        for ri in recipe.ingredients
    ]
    ok, info = await send_preparation_request(recipe.title, ingredient_lines, pr.note)
    pr.status = "sent" if ok else "pending"
    db.commit()

    return templates.TemplateResponse(
        request,
        "_prepare_result.html",
        {"ok": ok, "info": info, "recipe": recipe},
    )
