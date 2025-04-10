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
    #
    # def build_connection_str(self) -> str:
    #     """
    #     This function build a connection string
    #     """
    #     return URL.create(
    #         drivername=f"{self.database_system}+{self.driver}",
    #         username=self.user,
    #         database=self.name,
    #         password=self.passwd,
    #         port=self.port,
    #         host=self.host,
    #     ).render_as_string(hide_password=False)


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

    if getenv("IS_DEVELOP").capitalize() == "True":
        token: str = getenv("DEV_BOT_TOKEN")
        url: str = getenv("DEV_WEBHOOK_URL")
        port: str = getenv("DEV_WEBHOOK_PORT")
        path: str = getenv("DEV_WEBHOOK_PATH") + token
        webhook_url: str = url + port + path
        spam_id: int = int(getenv("DEV_SPAM_CHAT_ID"))
    else:
        token: str = getenv("BOT_TOKEN")
        url: str = getenv("WEBHOOK_URL")
        port: str = getenv("WEBHOOK_PORT")
        path: str = getenv("WEBHOOK_PATH") + token
        webhook_url: str = url + port + path
        spam_id: int = int(getenv("SPAM_CHAT_ID"))


@dataclass
class TokenConfig:
    SECRET_KEY: str = getenv("SECRET_KEY", "your-secret-key")
    ALGORITHM: str = getenv("", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(getenv("", 60))


@dataclass
class Configuration:
    """All in one configuration's class"""

    debug = bool(getenv("DEBUG"))
    # logging_level = int(getenv("LOGGING_LEVEL", logging.DEBUG))
    logging_level = logging.ERROR
    test = getenv("IS_DEVELOP").capitalize() == "True"
    telegram = True
    token_config = TokenConfig()
    db = DatabaseConfig()
    # redis = RedisConfig()
    bot = BotConfig()


conf = Configuration()
