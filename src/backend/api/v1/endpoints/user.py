from typing import List

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from starlette import status

from src.backend.api.v1.Models.user import UserRead, UserCreate, UserUpdate, UserRolesResponse
from src.backend.api.v1.dependencies.permissions import require_role
from src.backend.database.models.user import User
from src.backend.database.session_context import get_async_session

router = APIRouter(prefix="/users", tags=["users"], dependencies=[Depends(require_role("admin"))])


@router.get("/", response_model=List[UserRead])
async def read_users(session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(
        select(User).order_by(User.status).order_by(desc(User.is_admin)).order_by(User.created)
    )
    users = result.scalars().all()
    return users


@router.get("/{tg_id}", response_model=UserRead)
async def read_user(tg_id: int, session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(select(User).filter(User.tg_id == tg_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/", response_model=UserRead)
async def create_user(user_data: UserCreate, session: AsyncSession = Depends(get_async_session)):
    user = User(**user_data.dict())
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@router.patch("/{tg_id}", response_model=UserRead)
async def update_user(tg_id: int, user_data: UserUpdate, session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(select(User).filter(User.tg_id == tg_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    for key, value in user_data.dict(exclude_unset=True).items():
        setattr(user, key, value)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@router.delete("/{tg_id}", response_model=dict)
async def delete_user(tg_id: int, session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(select(User).filter(User.tg_id == tg_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await session.delete(user)
    await session.commit()
    return {"detail": "User deleted"}


@router.get("/{tg_id}/roles", response_model=UserRolesResponse)
async def get_user_roles(tg_id: int, session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(select(User).filter(User.tg_id == tg_id).options(selectinload(User.roles)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return {"roles": user.roles}
