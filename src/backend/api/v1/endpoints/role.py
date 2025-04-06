from typing import List

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from src.backend.api.v1.Models.role import RoleRead, RoleCreate, RoleAssign, RoleUpdate
from src.backend.api.v1.dependencies.permissions import require_role
from src.backend.database.models.role import Role
from src.backend.database.models.user import User
from src.backend.database.session_context import get_async_session

router = APIRouter(prefix="/roles", tags=["roles"])


@router.get("/", response_model=List[RoleRead])
async def read_roles(session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(select(Role))
    roles = result.scalars().all()
    return roles


@router.get("/{role_id}", response_model=RoleRead)
async def read_role(role_id: int, session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(select(Role).filter(Role.id == role_id))
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    return role


@router.post("/", response_model=RoleRead)
async def create_role(
    role: RoleCreate,
    session: AsyncSession = Depends(get_async_session),
    admin: bool = Depends(require_role("admin")),
):
    new_role = Role(name=role.name)
    session.add(new_role)
    await session.commit()
    await session.refresh(new_role)
    return new_role


@router.patch("/{role_id}", response_model=RoleRead)
async def update_role(
    role_id: int,
    role_update: RoleUpdate,
    session: AsyncSession = Depends(get_async_session),
    admin: bool = Depends(require_role("admin")),
):
    result = await session.execute(select(Role).filter(Role.id == role_id))
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    update_data = role_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(role, key, value)
    session.add(role)
    await session.commit()
    await session.refresh(role)
    return role


@router.delete("/{role_id}")
async def delete_role(
    role_id: int,
    session: AsyncSession = Depends(get_async_session),
    admin: bool = Depends(require_role("admin")),
):
    result = await session.execute(select(Role).filter(Role.id == role_id))
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    await session.delete(role)
    await session.commit()
    return {"detail": "Role deleted"}


@router.post("/{role_id}/assign", response_model=RoleRead)
async def assign_role_to_user(
    role_id: int,
    assign: RoleAssign,
    session: AsyncSession = Depends(get_async_session),
    admin: bool = Depends(require_role("admin")),
):
    result = await session.execute(select(Role).filter(Role.id == role_id))
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    result = await session.execute(select(User).filter(User.tg_id == assign.user_id).options(selectinload(User.roles)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if role not in user.roles:
        user.roles.append(role)
        session.add(user)
        await session.commit()
        await session.refresh(role)
    return role


@router.delete("/{role_id}/assign")
async def remove_role_from_user(
    role_id: int,
    user_id: int,
    session: AsyncSession = Depends(get_async_session),
    admin: bool = Depends(require_role("admin")),
):
    result = await session.execute(select(Role).filter(Role.id == role_id))
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    result = await session.execute(select(User).filter(User.tg_id == user_id).options(selectinload(User.roles)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if role in user.roles:
        user.roles.remove(role)
        session.add(user)
        await session.commit()
    return {"detail": "Role removed from user"}
