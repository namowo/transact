from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request

from app.core.config import settings
from app.api.exceptions import custom_exception_handler
from app.api.main import api_router
from app.crud.exceptions import AuthorizationError, DatabaseCommitError, NotFoundError
from app.exceptions import (
    authorization_exception_handler,
    database_commit_exception_handler,
    not_found_exception_handler,
)
from app.api.routers.frontend import SPAStaticFiles

# Create the database tables, if they do not exist. Not needed if using Alembic
# models.Base.metadata.create_all(bind=engine)

description = """
This is a fancy API built with [FastAPI🚀](https://fastapi.tiangolo.com/)

📝 [Source Code](https://github.com/johanngrobe/stellplatztool-backend)  
🐞 [Issues](https://github.com/johanngrobe/stellplatztool-backend/issues) 
"""

app = FastAPI(
    title="namowo Standortcheck",
    description=description,
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
)


app.add_exception_handler(AuthorizationError, custom_exception_handler)
app.add_exception_handler(DatabaseCommitError, custom_exception_handler)
app.add_exception_handler(NotFoundError, custom_exception_handler)


@app.exception_handler(NotFoundError)
async def not_found_exception_handler(request: Request, exc: NotFoundError):
    return JSONResponse(
        status_code=204,
        content={"message": f"Resource not found: {exc.detail}"},
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


app.mount(
    "/",
    SPAStaticFiles(directory=settings.FRONTEND_DIR, html=True),
    name="frontend",
)
