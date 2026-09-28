from fastapi import APIRouter, Depends, Request, Form, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Ingredient, RecipeIngredient
from ..security import verify_csrf
from ..templates import templates

router = APIRouter()


@router.get("/ingredients")
async def list_ingredients(request: Request, db: Session = Depends(get_db)):
    stmt = (
        select(Ingredient, func.count(RecipeIngredient.recipe_id))
        .outerjoin(RecipeIngredient, RecipeIngredient.ingredient_id == Ingredient.id)
        .group_by(Ingredient.id)
        .order_by(Ingredient.name)
    )
    rows = [{"ing": ing, "count": count} for ing, count in db.execute(stmt).all()]
    return templates.TemplateResponse(request, "ingredients.html", {"rows": rows})


@router.post("/ingredients/{ingredient_id}/delete")
async def delete_ingredient(
    ingredient_id: int,
    request: Request,
    csrf_token: str = Form(...),
    db: Session = Depends(get_db),
):
    verify_csrf(request, csrf_token)
    ing = db.get(Ingredient, ingredient_id)
    if not ing:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    in_use = db.scalar(
        select(func.count()).select_from(RecipeIngredient).where(
            RecipeIngredient.ingredient_id == ingredient_id
        )
    )
    if in_use:
        raise HTTPException(status.HTTP_409_CONFLICT, "Ingrédient utilisé par une recette")
    db.delete(ing)
    db.commit()
    return RedirectResponse("/ingredients", status_code=303)
