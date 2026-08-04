from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.author import Author
from app.schemas.author import AuthorCreate


async def get_or_create_author(db: AsyncSession, author_in: AuthorCreate) -> Author:
    data = author_in.model_dump()
    statement = select(Author).filter_by(**data)
    result = await db.execute(statement)
    author = result.scalars().first()
    if author is None:
        author = Author(**data)
        db.add(author)
        await db.flush()
    return author
