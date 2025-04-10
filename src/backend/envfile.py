import logging
from dataclasses import dataclass
from os import getenv

from dotenv import load_dotenv

load_dotenv()


@dataclass
class DatabaseConfig:
    """Database connection variables"""

    name: str = getenv("POSTGRES_DATABASE")
    user: str = getenv("POSTGRES_USER", "docker")
    passwd: str = getenv("POSTGRES_PASSWORD", None)
    port: int = int(getenv("POSTGRES_PORT", 5432))
    host: str = getenv("POSTGRES_HOST", "database")
    PG_URI: str = f"postgresql+asyncpg://{user}:{passwd}@{host}/{name}"
    #
    # driver: str = "asyncpg"
    # database_system: str = "postgresql"


# @dataclass
# class RedisConfig:
#     """Redis connection variables"""
#
#     db: str = int(getenv("REDIS_DATABASE", 1))
#     host: str = getenv("REDIS_HOST", "redis")
#     port: int = int(getenv("REDIS_PORT", 6379))
#     passwd: int = getenv("REDIS_PASSWORD")
#     username: int = getenv("REDIS_USERNAME")
#     state_ttl: int = getenv("REDIS_TTL_STATE", None)
#     data_ttl: int = getenv("REDIS_TTL_DATA", None)


@dataclass
class BotConfig:
    """Bot configuration"""

    token: str = getenv("BOT_TOKEN")
    url: str = getenv("WEBHOOK_URL")
    port: str = getenv("WEBHOOK_PORT")
    path: str = getenv("WEBHOOK_PATH") + token
    webhook_url: str = "https://" + url + path
    spam_id: int = int(getenv("SPAM_CHAT_ID"))


@dataclass
class TokenConfig:
    SECRET_KEY: str = getenv("SECRET_KEY", "your-secret-key")
    ALGORITHM: str = getenv("", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(getenv("", 60))


@dataclass
class Configuration:
    """All in one configuration's class"""

    logging_level = int(getenv("LOGGING_LEVEL", logging.ERROR))
    test = getenv("IS_DEVELOP").capitalize() == "True"
    telegram = True
    token_config = TokenConfig()
    db = DatabaseConfig()
    # redis = RedisConfig()
    bot = BotConfig()


conf = Configuration()
