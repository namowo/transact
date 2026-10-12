from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.site_settings import SiteSettings
from app.schemas.site_settings import SiteSettingsUpdate

SINGLETON_ID = 1


class CRUDSiteSettings:
    async def get(self, db: AsyncSession) -> SiteSettings:
        result = await db.execute(select(SiteSettings).where(SiteSettings.id == SINGLETON_ID))
        instance = result.scalar_one_or_none()
        if instance is None:
            instance = SiteSettings(id=SINGLETON_ID)
            db.add(instance)
            await db.commit()
            await db.refresh(instance)
        return instance

    async def update(self, db: AsyncSession, obj_in: SiteSettingsUpdate) -> SiteSettings:
        instance = await self.get(db)
        for field, value in obj_in.model_dump(exclude_unset=True).items():
            setattr(instance, field, value)
        await db.commit()
        await db.refresh(instance)
        return instance


crud_site_settings = CRUDSiteSettings()
