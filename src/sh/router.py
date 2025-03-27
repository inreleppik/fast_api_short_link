from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from fastapi.responses import RedirectResponse
import uuid


from sh.models import ShortLink
from sh.schemas import LinkCreate, LinkUpdate, LinkStats, LinkSearchRequest, LinkSearchResponse

from database import get_async_session
from auth.schemas import UserRead
from auth.users import fastapi_users, auth_backend

router = APIRouter(prefix="/links", tags=["Links"])

current_active_user = fastapi_users.current_user(active=True)
current_user_or_none = fastapi_users.current_user(optional=True)

@router.post("/shorten", response_model=LinkStats)
async def create_short_link(
    link_data: LinkCreate,
    session: AsyncSession = Depends(get_async_session),
    user: Optional[UserRead] = Depends(current_user_or_none),
):
    short_code = link_data.custom_alias or str(uuid.uuid4())[:8]

    existing = await session.execute(
        select(ShortLink).where(ShortLink.short_code == short_code)
    )
    link_in_db = existing.scalar_one_or_none()

    if link_in_db:
        if link_in_db.is_deleted:
            await session.delete(link_in_db)
            await session.flush()
        else:
            raise HTTPException(status_code=400, detail="Alias уже занят!")

    if user is None:
        forced_expires = datetime.now(timezone.utc) + timedelta(days=7)
        expires = forced_expires
        user_id = None
    else:
        user_id = user.id
        expires = link_data.expires_at

    new_link = ShortLink(
        short_code=short_code,
        original_url=str(link_data.original_url),
        expires_at=expires,
        user_id=user_id,
    )
    session.add(new_link)
    await session.commit()
    await session.refresh(new_link)
    return new_link

@router.get("/{short_code}")
async def redirect(short_code: str, session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(
        select(ShortLink).where(ShortLink.short_code == short_code)
    )
    link = result.scalar_one_or_none()
    if not link or link.is_deleted:
        raise HTTPException(status_code=404, detail="Ссылка не найдена или удалена")

    if link.is_expired():
        await session.delete(link)
        await session.commit()
        raise HTTPException(status_code=410, detail="Срок жизни ссылки истёк")

    link.clicks += 1
    link.last_used_at = datetime.now(timezone.utc)
    await session.commit()

    return RedirectResponse(url=link.original_url)

@router.get("/search/", response_model=List[LinkSearchResponse])
async def search_by_original_url(
    params: LinkSearchRequest = Depends(),
    session: AsyncSession = Depends(get_async_session)
):

    stmt = select(ShortLink).where(
        (ShortLink.original_url == params.original_url) &
        (ShortLink.is_deleted == False)
    )
    result = await session.execute(stmt)
    links = result.scalars().all()

    if not links:
        raise HTTPException(status_code=404, detail="Ссылки не найдены")

    return links

@router.get("/expired/", response_model=List[LinkStats])
async def get_expired_links(session: AsyncSession = Depends(get_async_session)):

    stmt = select(ShortLink).where(ShortLink.is_deleted.is_(True))
    result = await session.execute(stmt)
    links = result.scalars().all()
    return links


@router.get("/{short_code}/stats", response_model=LinkStats)
async def get_stats(short_code: str, session: AsyncSession = Depends(get_async_session)):

    result = await session.execute(
        select(ShortLink).where(
            (ShortLink.short_code == short_code) & 
            (ShortLink.is_deleted == False)
        )
    )
    link = result.scalar_one_or_none()
    if not link:
        raise HTTPException(
            status_code=404,
            detail="Ссылка не найдена или удалена"
        )
    return link

@router.delete("/{short_code}")
async def delete_link(
    short_code: str,
    session: AsyncSession = Depends(get_async_session),
    user: UserRead = Depends(current_active_user),
):

    result = await session.execute(
        select(ShortLink).where(ShortLink.short_code == short_code)
    )
    link = result.scalar_one_or_none()

    if not link:
        raise HTTPException(status_code=404, detail="Ссылка не найдена")

    if link.user_id is None:
        raise HTTPException(status_code=403, detail="Анонимную ссылку нельзя удалить")

    if link.user_id != user.id:
        raise HTTPException(status_code=403, detail="Нет доступа")

    link.is_deleted = True
    await session.commit()
    return {"detail": "Ссылка помечена как удалённая"}

@router.put("/{short_code}")
async def update_link(
    short_code: str,
    data: LinkUpdate,
    session: AsyncSession = Depends(get_async_session),
    user: UserRead = Depends(current_active_user),
):

    result = await session.execute(
        select(ShortLink).where(ShortLink.short_code == short_code)
    )
    link = result.scalar_one_or_none()

    if not link or link.is_deleted:
        raise HTTPException(status_code=404, detail="Ссылка не найдена или удалена")

    if link.user_id is None:
        raise HTTPException(status_code=403, detail="Нельзя менять анонимную ссылку")

    if link.user_id != user.id:
        raise HTTPException(status_code=403, detail="Нет доступа")

    link.original_url = str(data.original_url)
    link.last_used_at = datetime.now(timezone.utc)
    await session.commit()
    return {"detail": "Обновлено"}

