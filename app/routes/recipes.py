import json
from fastapi import APIRouter, Depends, Request, Form, UploadFile, File, HTTPException, status
from fastapi.responses import RedirectResponse
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Recipe, Ingredient, RecipeIngredient
from ..schemas import RecipeCreate, IngredientIn, slugify
from ..security import verify_csrf
from ..uploads import save_image, delete_image
from ..templates import templates

router = APIRouter()


def _get_or_create_ingredient(db: Session, name: str) -> Ingredient:
    slug = slugify(name)
    ing = db.query(Ingredient).filter_by(slug=slug).one_or_none()
    if ing:
        return ing
    ing = Ingredient(name=name, slug=slug)
    db.add(ing)
    db.flush()
    return ing


def _parse_payload(
    title: str,
    steps_json: str,
    ingredients_json: str,
    comment: str | None,
    category: str | None,
    origin: str | None,
) -> RecipeCreate:
    try:
        raw_ings = json.loads(ingredients_json)
        raw_steps = json.loads(steps_json)
    except json.JSONDecodeError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid form data")
    if not isinstance(raw_steps, list) or not isinstance(raw_ings, list):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid form data")
    try:
        return RecipeCreate(
            title=title,
            category=category,
            origin=origin,
            steps=raw_steps,
            comment=comment,
            ingredients=[IngredientIn(**i) for i in raw_ings],
        )
    except (ValidationError, TypeError):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid form data")


def _known_origins(db: Session) -> list[str]:
    return db.scalars(
        select(Recipe.origin).where(Recipe.origin.is_not(None)).distinct().order_by(Recipe.origin)
    ).all()


def _sync_ingredients(db: Session, recipe: Recipe, payload: RecipeCreate) -> None:
    recipe.ingredients.clear()
    db.flush()
    seen = set()
    for ing_in in payload.ingredients:
        slug = slugify(ing_in.name)
        if slug in seen:
            continue
        seen.add(slug)
        ing = _get_or_create_ingredient(db, ing_in.name)
        db.add(RecipeIngredient(recipe_id=recipe.id, ingredient_id=ing.id, quantity=ing_in.quantity))


@router.get("/recipes/new")
async def new_recipe_form(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse(
        request,
        "recipe_form.html",
        {"recipe": None, "edit_mode": False, "known_origins": _known_origins(db)},
    )


@router.post("/recipes")
async def create_recipe(
    request: Request,
    title: str = Form(...),
    steps_json: str = Form(...),
    ingredients_json: str = Form(...),
    comment: str | None = Form(None),
    category: str | None = Form(None),
    origin: str | None = Form(None),
    csrf_token: str = Form(...),
    image: UploadFile | None = File(None),
    db: Session = Depends(get_db),
):
    verify_csrf(request, csrf_token)
    payload = _parse_payload(title, steps_json, ingredients_json, comment, category, origin)

    image_name = None
    if image is not None and image.filename:
        image_name = await save_image(image)

    recipe = Recipe(
        title=payload.title,
        category=payload.category,
        origin=payload.origin,
        steps_json=json.dumps(payload.steps, ensure_ascii=False),
        comment=payload.comment,
        image_path=image_name,
    )
    db.add(recipe)
    db.flush()
    _sync_ingredients(db, recipe, payload)
    db.commit()
    return RedirectResponse(f"/recipes/{recipe.id}", status_code=303)


@router.get("/recipes/{recipe_id}")
async def view_recipe(recipe_id: int, request: Request, db: Session = Depends(get_db)):
    recipe = db.get(Recipe, recipe_id)
    if not recipe:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    try:
        steps = json.loads(recipe.steps_json or "[]")
    except json.JSONDecodeError:
        steps = []
    return templates.TemplateResponse(request, "recipe_detail.html", {"recipe": recipe, "steps": steps})


@router.get("/recipes/{recipe_id}/edit")
async def edit_recipe_form(recipe_id: int, request: Request, db: Session = Depends(get_db)):
    recipe = db.get(Recipe, recipe_id)
    if not recipe:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    try:
        steps = json.loads(recipe.steps_json or "[]")
    except json.JSONDecodeError:
        steps = []
    ingredients = [
        {"name": ri.ingredient.name, "quantity": ri.quantity or ""}
        for ri in recipe.ingredients
    ]
    return templates.TemplateResponse(
        request,
        "recipe_form.html",
        {
            "recipe": recipe,
            "edit_mode": True,
            "initial_steps": steps,
            "initial_ingredients": ingredients,
            "known_origins": _known_origins(db),
        },
    )


@router.post("/recipes/{recipe_id}/edit")
async def update_recipe(
    recipe_id: int,
    request: Request,
    title: str = Form(...),
    steps_json: str = Form(...),
    ingredients_json: str = Form(...),
    comment: str | None = Form(None),
    category: str | None = Form(None),
    origin: str | None = Form(None),
    csrf_token: str = Form(...),
    image: UploadFile | None = File(None),
    db: Session = Depends(get_db),
):
    verify_csrf(request, csrf_token)
    recipe = db.get(Recipe, recipe_id)
    if not recipe:
        raise HTTPException(status.HTTP_404_NOT_FOUND)

    payload = _parse_payload(title, steps_json, ingredients_json, comment, category, origin)

    if image is not None and image.filename:
        old_image = recipe.image_path
        recipe.image_path = await save_image(image)
        delete_image(old_image)

    recipe.title = payload.title
    recipe.category = payload.category
    recipe.origin = payload.origin
    recipe.steps_json = json.dumps(payload.steps, ensure_ascii=False)
    recipe.comment = payload.comment
    _sync_ingredients(db, recipe, payload)
    db.commit()
    return RedirectResponse(f"/recipes/{recipe.id}", status_code=303)


@router.post("/recipes/{recipe_id}/delete")
async def delete_recipe(
    recipe_id: int,
    request: Request,
    csrf_token: str = Form(...),
    db: Session = Depends(get_db),
):
    verify_csrf(request, csrf_token)
    recipe = db.get(Recipe, recipe_id)
    if not recipe:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    image_name = recipe.image_path
    db.delete(recipe)
    db.commit()
    delete_image(image_name)
    return RedirectResponse("/", status_code=303)
