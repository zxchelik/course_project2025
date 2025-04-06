from aiogram import Bot

from envfile import conf as settings

bot = Bot(token=settings.bot.token, parse_mode="HTML")
