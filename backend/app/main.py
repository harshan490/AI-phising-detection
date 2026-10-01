import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.api.endpoints import scanner, auth, model
from app.db.session import engine
from app.db.base import Base
import app.models.user  # noqa: F401  (register tables)
import app.models.scan  # noqa: F401

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("app")

Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.PROJECT_NAME, openapi_url=f"{settings.API_V1_STR}/openapi.json")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.exception_handler(Exception)
async def unhandled_error(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


app.include_router(scanner.router, prefix=f"{settings.API_V1_STR}/scanner", tags=["scanner"])
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(model.router, prefix=f"{settings.API_V1_STR}/model", tags=["model"])


@app.get("/")
def root():
    return {"message": f"Welcome to {settings.PROJECT_NAME}"}


@app.get("/health")
def health_check():
    return {"status": "ok"}
