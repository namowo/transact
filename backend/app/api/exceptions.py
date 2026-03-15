from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse


async def custom_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=(
            exc.status_code
            if hasattr(exc, "status_code")
            else status.HTTP_500_INTERNAL_SERVER_ERROR
        ),
        content={"message": exc.message if hasattr(exc, "message") else str(exc)},
    )
