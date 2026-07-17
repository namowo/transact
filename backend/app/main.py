from pathlib import Path

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.main import api_router
from app.crud.exceptions import AuthorizationError, DatabaseCommitError, NotFoundError
from app.exceptions import (
    authorization_exception_handler,
    database_commit_exception_handler,
    not_found_exception_handler,
)
from app.api.routers.frontend import SPAStaticFiles

description = """
API for TransAct, a research data management tool for studies on the
transfer, persistence and recovery of trace DNA.
"""

app = FastAPI(
    title="TransAct",
    description=description,
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
)

# Set all CORS enabled origins
if settings.all_cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.all_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )

app.add_exception_handler(AuthorizationError, authorization_exception_handler)
app.add_exception_handler(DatabaseCommitError, database_commit_exception_handler)
app.add_exception_handler(NotFoundError, not_found_exception_handler)

app.include_router(api_router, prefix=settings.API_V1_STR)


frontend_dir = Path(__file__).resolve().parent.parent / settings.FRONTEND_DIR
if frontend_dir.is_dir():
    # Only present once the frontend has been built (`npm run build`). In
    # local development the frontend is served separately by `npm run dev`.
    app.mount(
        "/",
        SPAStaticFiles(directory=str(frontend_dir), html=True),
        name="frontend",
    )
