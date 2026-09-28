from pydantic import BaseModel, Field, field_validator
from unidecode import unidecode
import re


def slugify(name: str) -> str:
    s = unidecode(name).lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s


CATEGORIES = {
    "entree": "Entrée",
    "plat": "Plat",
    "dessert": "Dessert",
}


class IngredientIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    quantity: str | None = Field(default=None, max_length=50)

    @field_validator("name")
    @classmethod
    def clean_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("empty name")
        return v


class RecipeCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    category: str | None = Field(default=None)
    origin: str | None = Field(default=None, max_length=100)
    steps: list[str] = Field(min_length=1, max_length=50)
    ingredients: list[IngredientIn] = Field(min_length=1, max_length=100)
    comment: str | None = Field(default=None, max_length=5000)

    @field_validator("title")
    @classmethod
    def strip_text(cls, v: str) -> str:
        return v.strip()

    @field_validator("category")
    @classmethod
    def clean_category(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        if not v:
            return None
        if v not in CATEGORIES:
            raise ValueError("unknown category")
        return v

    @field_validator("origin")
    @classmethod
    def clean_origin(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        return v or None

    @field_validator("steps")
    @classmethod
    def clean_steps(cls, v: list[str]) -> list[str]:
        cleaned = [s.strip() for s in v if s and s.strip()]
        if not cleaned:
            raise ValueError("at least one step required")
        for s in cleaned:
            if len(s) > 2000:
                raise ValueError("step too long")
        return cleaned

    @field_validator("comment")
    @classmethod
    def clean_comment(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        return v or None
