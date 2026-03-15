from fastapi import APIRouter, status

router = APIRouter()


@router.get("/health-check", status_code=status.HTTP_200_OK)
def health_check():
    return {"status": "working"}
