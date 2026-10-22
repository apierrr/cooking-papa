from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

from .config import UPLOAD_DIR
from .db import init_db
from .security import SECURITY_HEADERS, CSRF_COOKIE, CSRF_MAX_AGE, issue_csrf_token
from .routes import recipes, search, prepare, ingredients


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Cooking Papa", docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        for k, v in SECURITY_HEADERS.items():
            response.headers.setdefault(k, v)
        if not request.cookies.get(CSRF_COOKIE):
            response.set_cookie(
                CSRF_COOKIE,
                issue_csrf_token(),
                max_age=CSRF_MAX_AGE,
                httponly=False,
                samesite="strict",
                secure=True,
            )
        return response


app.add_middleware(SecurityHeadersMiddleware)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

app.include_router(search.router)
app.include_router(recipes.router)
app.include_router(prepare.router)
app.include_router(ingredients.router)


@app.get("/healthz")
def healthz():
    return {"ok": True}
