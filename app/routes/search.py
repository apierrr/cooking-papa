from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Recipe, Ingredient, RecipeIngredient
from ..schemas import slugify, CATEGORIES
from ..templates import templates

router = APIRouter()


@router.get("/")
async def index(
    request: Request,
    q: str | None = Query(None, max_length=200),
    cat: str | None = Query(None, max_length=20),
    origin: str | None = Query(None, max_length=100),
    ing: list[str] = Query(default_factory=list),
    db: Session = Depends(get_db),
):
    ing_slugs = [slugify(i) for i in ing if i.strip()]
    ing_slugs = [s for s in ing_slugs if s][:20]
    cat = cat if cat in CATEGORIES else None
    origin = (origin or "").strip() or None

    stmt = select(Recipe).order_by(Recipe.created_at.desc())

    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(Recipe.title.ilike(like))

    if cat:
        stmt = stmt.where(Recipe.category == cat)

    if origin:
        stmt = stmt.where(Recipe.origin == origin)

    if ing_slugs:
        subq = (
            select(RecipeIngredient.recipe_id)
            .join(Ingredient, Ingredient.id == RecipeIngredient.ingredient_id)
            .where(Ingredient.slug.in_(ing_slugs))
            .group_by(RecipeIngredient.recipe_id)
            .having(func.count(func.distinct(Ingredient.slug)) == len(ing_slugs))
        )
        stmt = stmt.where(Recipe.id.in_(subq))

    recipes = db.scalars(stmt.limit(200)).all()

    all_ingredients = db.scalars(select(Ingredient).order_by(Ingredient.name)).all()
    all_origins = db.scalars(
        select(Recipe.origin).where(Recipe.origin.is_not(None)).distinct().order_by(Recipe.origin)
    ).all()

    ctx = {
        "recipes": recipes,
        "all_ingredients": all_ingredients,
        "all_origins": all_origins,
        "selected_ings": ing_slugs,
        "selected_cat": cat or "",
        "selected_origin": origin or "",
        "q": q or "",
    }
    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(request, "_recipe_list.html", ctx)
    return templates.TemplateResponse(request, "index.html", ctx)


@router.get("/ingredients/suggest")
async def suggest_ingredients(
    q: str = Query("", max_length=50),
    db: Session = Depends(get_db),
    request: Request = None,
):
    q_slug = slugify(q) if q else ""
    stmt = select(Ingredient).order_by(Ingredient.name).limit(15)
    if q_slug:
        stmt = stmt.where(Ingredient.slug.startswith(q_slug))
    ings = db.scalars(stmt).all()
    return templates.TemplateResponse(request, "_suggest.html", {"ingredients": ings})
