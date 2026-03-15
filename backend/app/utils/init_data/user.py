import asyncio
from app.schemas.user import UserCreate
from app.utils.auth import create_user

user = UserCreate(
    email="j.grobe@namowo.de",
    password="Test123!",
    is_superuser=True,
    is_verified=True,
    vorname="Johann",
    nachname="Grobe",
    organisation="namowo",
    telefon="015123482133",
    strasse="Jahnstraße",
    hausnummer="32",
    plz="65185",
    stadt="Wiesbaden",
    land="Deutschland",
)


async def main():
    await create_user(user)


if __name__ == "__main__":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
