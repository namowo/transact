from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi import HTTPException


class SPAStaticFiles(StaticFiles):
    """
    Serves a Single Page Application (SPA) by:
    - serving static files normally
    - falling back to index.html when a path is not found
    """

    async def get_response(self, path: str, scope):
        try:
            return await super().get_response(path, scope)
        except (HTTPException, StarletteHTTPException) as ex:
            # Fallback to index.html if file not found
            if ex.status_code == 404:
                return await super().get_response("index.html", scope)
            raise
