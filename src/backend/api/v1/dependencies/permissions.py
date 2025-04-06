from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from jose.exceptions import JWTError, ExpiredSignatureError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.backend.envfile import conf
from src.backend.database.models.user import User
from src.backend.database.session_context import get_async_session

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
SECRET_KEY = conf.token_config.SECRET_KEY
ALGORITHM = conf.token_config.ALGORITHM or "HS256"


async def get_current_user(
    token: str = Depends(oauth2_scheme), session: AsyncSession = Depends(get_async_session)
) -> User:
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"verify_exp": True},  # включает проверку exp
        )
        tg_id: str | None = payload.get("sub")
        if tg_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Невозможно подтвердить подлинность учетных данных",
            )
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Токен истек",
        )

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Невозможно подтвердить подлинность учетных данных",
        )
    result = await session.execute(select(User).filter(User.tg_id == int(tg_id)))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден",
        )
    return user


def require_role(required_role: str):
    async def role_dependency(token: str = Depends(oauth2_scheme)):
        try:
            payload = jwt.decode(
                token,
                SECRET_KEY,
                algorithms=[ALGORITHM],
                options={"verify_exp": True},  # включает проверку exp
            )
            roles: list[str] = payload.get("roles", [])
        except ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Токен истек",
            )
        except JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Невалидный токен")
        # Админы имеют полный доступ
        if "admin" in roles or required_role in roles:
            return
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав для доступа к данному функционалу"
        )

    return role_dependency
