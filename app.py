import uvicorn
from aiogram import Dispatcher, types, F
from aiogram.fsm.storage.memory import MemoryStorage
# from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import FSInputFile, ErrorEvent, Update
from fastapi import FastAPI
from loguru import logger

from database.session_context import sessionmaker
from envfile import conf as config
from handlers.register_router import register_router
from middlewares.database_middleware import DbSessionMiddleware
from misc import bot

logger.add("logs.log", format="{time} {level} {file} {function} {line} {message}", level=config.logging_level, mode="a",
           rotation="1GB", compression="zip")

storage = MemoryStorage()

WEBHOOK_PATH = config.bot.path
WEBHOOK_URL = config.bot.webhook_url

WEBHOOK_SSL_CERT = "ssl/cert.crt"
WEBHOOK_SSL_PRIV = "ssl/cert.key"

app = FastAPI()
# bot = Bot(token=config.bot.token, parse_mode="HTML")
dp = Dispatcher(storage=storage)


# async def create_db(engine):
#     async with engine.begin() as conn:
#         await conn.run_sync(Base.metadata.drop_all)
#         await conn.run_sync(Base.metadata.create_all)


@app.on_event("startup")
async def on_startup():
    webhook_info = await bot.get_webhook_info()
    if webhook_info != WEBHOOK_URL:
        await bot.delete_webhook(drop_pending_updates=True)
        # if not config.test:
        await bot.set_webhook(
            WEBHOOK_URL,
            certificate=FSInputFile(WEBHOOK_SSL_CERT),
        )
        # else:
        # await bot.set_webhook(WEBHOOK_URL)

    register_router(dp)  # функция для регистрации роутеров
    dp.update.middleware(DbSessionMiddleware(session_maker=sessionmaker))
    # await create_db(engine)  # подключаемся к бд
    logger.info(f"App started for bot: {(await bot.get_me()).username}")


@app.post(WEBHOOK_PATH)
async def bot_webhook(update: dict):
    telegram_update = types.Update(**update)
    await dp.feed_update(bot=bot, update=telegram_update)


@app.on_event("shutdown")
async def on_shutdown():
    await bot.session.close()
    logger.info("App stopped")


@dp.errors(F.update.as_("update"))
async def error_handler(event: ErrorEvent, update: Update):
    logger.exception(event.exception)
    text = f"Что-то пошло не по плану: попробуйте ещё раз.\n\n{event.exception}\n\n/menu"
    match update.event_type:
        case "message":
            await update.message.answer(text)
        case "callback_query":
            await update.callback_query.message.answer(text)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(config.bot.port), ssl_certfile=WEBHOOK_SSL_CERT,
                ssl_keyfile=WEBHOOK_SSL_PRIV)
