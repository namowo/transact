import asyncio

from app.core.deps import get_async_session
from app.crud.laboratory import crud_laboratory
from app.crud.user import crud_user
from app.schemas.laboratory import LaboratoryCreate
from app.schemas.user import UserCreate

SUPERUSER_EMAIL = "j.grobe@namowo.de"
SUPERUSER_PASSWORD = "Test123!"


async def main() -> None:
    async for db in get_async_session():
        if await crud_user.get_by_email(db, SUPERUSER_EMAIL):
            print(f"User {SUPERUSER_EMAIL} already exists")
            return

        laboratory = await crud_laboratory.create(
            db,
            LaboratoryCreate(
                laboratory_name="TransAct Admin",
                country="Germany",
                postal_code="65185",
                state="Hesse",
                city="Wiesbaden",
                street_address="Jahnstraße 32",
                institutional_affiliation="TransAct",
                director_head_of_laboratory="Johann Grobe",
                email=SUPERUSER_EMAIL,
            ),
        )

        user = await crud_user.create(
            db,
            UserCreate(
                email=SUPERUSER_EMAIL,
                password=SUPERUSER_PASSWORD,
                first_name="Johann",
                last_name="Grobe",
                laboratory_id=laboratory.id,
            ),
            is_verified=True,
            is_superuser=True,
        )
        print(f"Superuser created: {user.email}")


if __name__ == "__main__":
    asyncio.run(main())
