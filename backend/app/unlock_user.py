"""Unlock an account locked after too many wrong passwords - for when no
admin can sign in to do it in the app.

    python -m app.unlock_user admin@example.com

Add --reset-two-factor to also remove the user's authenticator app and
passkeys.
"""

import argparse
import asyncio

from app.core.db import async_session_maker
from app.crud import two_factor
from app.crud.user import crud_user


async def main(email: str, reset_two_factor: bool) -> int:
    async with async_session_maker() as db:
        user = await crud_user.get_by_email(db, email)
        if user is None:
            print(f"No user with the email {email}.")
            return 1
        await crud_user.unlock(db, user)
        print(f"Unlocked {user.email}.")
        if reset_two_factor:
            await two_factor.reset(db, user)
            print("Removed their authenticator app and passkeys.")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("email")
    parser.add_argument("--reset-two-factor", action="store_true")
    args = parser.parse_args()
    raise SystemExit(asyncio.run(main(args.email, args.reset_two_factor)))
