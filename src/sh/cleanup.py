from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.config import CLEANUP_EXPIRE_DAYS
from src.sh.models import ShortLink


async def cleanup_old_links(session: AsyncSession):
    """
    Помечает как удалённые ссылки, которые:
    - не использовались более N дней,
    - не использовались вовсе и были созданы более N дней назад,
    - или уже истекли по expires_at.
    """
    now = datetime.now(timezone.utc)
    deadline = now - timedelta(days=CLEANUP_EXPIRE_DAYS)

    stmt = select(ShortLink).where(
        (
            (ShortLink.last_used_at < deadline) |
            ((ShortLink.last_used_at == None) & (ShortLink.created_at < deadline)) |
            ((ShortLink.expires_at != None) & (ShortLink.expires_at < now))
        ) &
        (ShortLink.is_deleted == False)
    )

    result = await session.execute(stmt)
    links = result.scalars().all()

    for link in links:
        link.is_deleted = True

    await session.commit()