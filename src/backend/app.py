import asyncio
from asyncio import Task

import uvicorn
from aiogram import Dispatcher, types, F
from aiogram.fsm.storage.memory import MemoryStorage

# from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import FSInputFile, ErrorEvent, Update
from fastapi import FastAPI
from loguru import logger
from starlette.middleware.cors import CORSMiddleware

from envfile import conf as config
from misc import bot
from src.backend.api import main_api_router
from src.backend.database.session_context import sessionmaker
from src.backend.telegram.handlers.register_router import register_router
from src.backend.telegram.middlewares.database_middleware import DbSessionMiddleware

logger.add(
    "../../logs.log",
    format="{time} {level} {file} {function} {line} {message}",
    level=config.logging_level,
    mode="a",
    rotation="1GB",
    compression="zip",
)

storage = MemoryStorage()

WEBHOOK_PATH = config.bot.path
WEBHOOK_URL = config.bot.webhook_url

WEBHOOK_SSL_CERT = "src/backend/ssl/cert.crt"
WEBHOOK_SSL_PRIV = "src/backend/ssl/cert.key"

app = FastAPI()
# bot = Bot(token=config.bot.token, parse_mode="HTML")
dp = Dispatcher(storage=storage)

polling_task: Task | None = None
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:80",
    "http://127.0.0.1:80",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(main_api_router)


@app.on_event("startup")
async def on_startup():

    if config.telegram:
        dp.update.middleware(DbSessionMiddleware(session_maker=sessionmaker))
        register_router(dp)  # функция для регистрации роутеров
        webhook_info = await bot.get_webhook_info()
        if webhook_info != WEBHOOK_URL:
            await bot.delete_webhook(drop_pending_updates=True)
            if not config.test:
                await bot.set_webhook(
                    WEBHOOK_URL,
                    certificate=FSInputFile(WEBHOOK_SSL_CERT),
                )
            else:
                logger.info(f"App started for bot: {(await bot.get_me()).username}")
                global polling_task
                polling_task = asyncio.create_task(dp.start_polling(bot))


@app.post(WEBHOOK_PATH)
async def bot_webhook(update: dict):
    telegram_update = types.Update(**update)
    await dp.feed_update(bot=bot, update=telegram_update)


@app.on_event("shutdown")
async def on_shutdown():
    global polling_task
    if polling_task:
        polling_task.cancel()
        try:
            await polling_task
        except asyncio.CancelledError:
            logger.info("Polling task cancelled")
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
    if config.test:
        uvicorn.run(app, host="0.0.0.0", port=int(config.bot.port))
    else:
        uvicorn.run(
            app, host="0.0.0.0", port=int(config.bot.port), ssl_certfile=WEBHOOK_SSL_CERT, ssl_keyfile=WEBHOOK_SSL_PRIV
        )
