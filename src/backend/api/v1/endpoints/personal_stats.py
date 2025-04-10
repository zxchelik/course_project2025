import random

from fastapi import APIRouter, Depends, HTTPException
from starlette import status

from api.v1.Models.stats.personal_stats import PersonalStat
from api.v1.Models.user import UserRead
from api.v1.dependencies.permissions import get_current_user

router = APIRouter(prefix="/stats/users", tags=["Статистика"])


@router.get("/{tg_id}", response_model=list[PersonalStat])
async def get_personal_stats(tg_id: int, current_user: UserRead = Depends(get_current_user)):
    if not current_user.is_admin and tg_id != current_user.tg_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access your own stats.",
        )

    rnd = random.Random(tg_id)

    result = []
    result.append(PersonalStat(title="Изготовленно бочек за месяц", info=f"{rnd.randint(0,100)} шт"))
    result.append(PersonalStat(title="Изготовленно кассет за месяц", info=f"{rnd.randint(0,50)} шт"))
    result.append(PersonalStat(title="Почасовых работ за месяц", info=f"{rnd.randint(0,500)} часа"))
    result.append(PersonalStat(title="Собранно кассет за месяц", info=f"{rnd.randint(0,50)} шт"))
    result.append(PersonalStat(title="Дней во компании", info=f"{rnd.randint(30,300)} дня"))
    result.append(PersonalStat(title="Зарплата в этом месяце", info=f"{rnd.randint(50,150)*1000} руб"))
    return result
