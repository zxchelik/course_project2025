import datetime
from contextlib import asynccontextmanager

from loguru import logger
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from envfile import conf as config

engine = create_async_engine(url=config.db.PG_URI, echo=False)
sessionmaker = async_sessionmaker(engine, expire_on_commit=False)


@asynccontextmanager
async def get_async_session():
    session = sessionmaker()
    try:
        yield session
    except Exception as e:
        logger.error(e)
        await session.rollback()
        raise
    finally:
        await session.close()


def async_session_context(func):
    async def warper(*args, **kwargs):
        async with get_async_session() as session:
            async with session.begin():
                t1 = datetime.datetime.now()
                res = await func(session, *args, **kwargs)
                dt = datetime.datetime.now() - t1
                if dt.total_seconds() >= 5:
                    logger.error(F"sql query execution time :{dt}")
                return res

    return warper
