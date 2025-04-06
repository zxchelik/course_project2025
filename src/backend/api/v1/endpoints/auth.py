from datetime import datetime, timedelta, UTC
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from passlib.context import CryptContext
from sqlalchemy.orm import selectinload

from src.backend.api.v1.Models.auth import TokenSchema, RegistrationSchema
from src.backend.api.v1.Models.user import UserRead
from src.backend.database.models.user import User
from src.backend.database.session_context import get_async_session
from src.backend.envfile import conf

router = APIRouter(prefix="/auth", tags=["auth"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(data: dict, roles: list[str], expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    to_encode.update({"roles": roles})
    expire = datetime.now(UTC) + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, conf.token_config.SECRET_KEY, algorithm=conf.token_config.ALGORITHM)
    return encoded_jwt


def generate_token(user: User):
    # Формируем список ролей из таблицы ролей, например:
    roles = [role.name for role in user.roles]
    # Если админ, можно добавить роль "admin" автоматически:
    if user.is_admin and "admin" not in roles:
        roles.append("admin")
    access_token_expires = timedelta(minutes=conf.token_config.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": str(user.tg_id)}, roles=roles, expires_delta=access_token_expires)
    return TokenSchema(access_token=access_token, token_type="bearer", user=UserRead.from_orm(user))


@router.post("/register", response_model=TokenSchema)
async def register_user(reg: RegistrationSchema, session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(select(User).filter(User.tg_id == reg.tg_id).options(selectinload(User.roles)))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="Пользователь с указанным tg_id не найден")
    if user.user_login is not None or user.hashed_password is not None:
        raise HTTPException(status_code=400, detail="Пользователь уже зарегистрирован")
    user.user_login = reg.user_login
    user.hashed_password = pwd_context.hash(reg.password)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return generate_token(user)


@router.post("/login", response_model=TokenSchema)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(
        select(User).filter(User.user_login == form_data.username).options(selectinload(User.roles))
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    if not pwd_context.verify(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный пароль")
    return generate_token(user)
