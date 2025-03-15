import os
from enum import Enum
from pydantic_settings import BaseSettings, SettingsConfigDict

class PydanticBaseSettings(BaseSettings):
    # ENV = PROD
    # model_config = SettingsConfigDict(env_file='src/.env', extra='ignore')
    # ENV = DEV
    model_config = SettingsConfigDict(env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env'), extra='ignore')

print("Settings loaded", PydanticBaseSettings())
class AppSettings(PydanticBaseSettings):
    APP_NAME: str = "FastAPI app"
    APP_DESCRIPTION: str | None = None
    APP_VERSION: str | None = None
    LICENSE_NAME: str | None = None
    CONTACT_NAME: str | None = None
    CONTACT_EMAIL: str | None = None


class CryptSettings(PydanticBaseSettings):
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    CLERK_SECRET_KEY: str
    CLERK_SIGNING_SECRET: str


class DatabaseSettings(PydanticBaseSettings):
    pass


class SQLiteSettings(DatabaseSettings):
    SQLITE_URI: str = "./sql_app.db"
    SQLITE_SYNC_PREFIX: str = "sqlite:///"
    SQLITE_ASYNC_PREFIX: str = "sqlite+aiosqlite:///"


class PostgresSettings(DatabaseSettings):
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "postgres"
    POSTGRES_SYNC_PREFIX: str = "postgresql://"
    POSTGRES_ASYNC_PREFIX: str = "postgresql+asyncpg://"
    POSTGRES_URI: str | None = None

    def model_post_init(self, *args, **kwargs) -> None:
        super().model_post_init(*args, **kwargs)
        self.POSTGRES_URI = f"{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"


class FirstUserSettings(PydanticBaseSettings):
    ADMIN_NAME: str = "admin"
    ADMIN_EMAIL: str = "admin@admin.com"
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "!Ch4ng3Th1sP4ssW0rd!"


class TestSettings(PydanticBaseSettings):
    TEST_NAME: str = "Tester User"
    TEST_EMAIL: str = "test@tester.com"
    TEST_USERNAME: str = "testeruser"
    TEST_PASSWORD: str = "Str1ng$t"


class RedisCacheSettings(PydanticBaseSettings):
    REDIS_CACHE_HOST: str = "localhost"
    REDIS_CACHE_PORT: int = 6379
    REDIS_CACHE_URL: str | None = None

    def model_post_init(self, *args, **kwargs) -> None:
        super().model_post_init(*args, **kwargs)
        self.REDIS_CACHE_URL = f"redis://{self.REDIS_CACHE_HOST}:{self.REDIS_CACHE_PORT}"


class ClientSideCacheSettings(PydanticBaseSettings):
    CLIENT_CACHE_MAX_AGE: int = 60


class RedisQueueSettings(PydanticBaseSettings):
    REDIS_QUEUE_HOST: str = "localhost"
    REDIS_QUEUE_PORT: int = 6379


class RedisRateLimiterSettings(PydanticBaseSettings):
    REDIS_RATE_LIMIT_HOST: str = "localhost"
    REDIS_RATE_LIMIT_PORT: int = 6379
    REDIS_RATE_LIMIT_URL: str | None = None

    def model_post_init(self, *args, **kwargs) -> None:
        super().model_post_init(*args, **kwargs)
        self.REDIS_RATE_LIMIT_URL = f"redis://{self.REDIS_RATE_LIMIT_HOST}:{self.REDIS_RATE_LIMIT_PORT}"


class DefaultRateLimitSettings(PydanticBaseSettings):
    DEFAULT_RATE_LIMIT_LIMIT: int = 10
    DEFAULT_RATE_LIMIT_PERIOD: int = 3600


class EnvironmentOption(Enum):
    LOCAL = "local"
    STAGING = "staging"
    PRODUCTION = "production"


class DBOption(Enum):
    POSTGRES = "postgres"
    SQLITE = "sqlite"


class EnvironmentSettings(PydanticBaseSettings):
    ENVIRONMENT: EnvironmentOption = EnvironmentOption.LOCAL
    DB_ENGINE: DBOption = DBOption.SQLITE

class AISettings(PydanticBaseSettings):
    OPENAI_API_KEY: str | None = None

class GitHubSettings(PydanticBaseSettings):
    GITHUB_CLIENT_ID: str
    GITHUB_CLIENT_SECRET: str
    GITHUB_REDIRECT_URI: str

class AccessTokenSettings(PydanticBaseSettings):
    GITHUB_ACCESS_TOKEN: str | None = None


db_type = PostgresSettings
if EnvironmentSettings().DB_ENGINE == DBOption.SQLITE:
    db_type = SQLiteSettings


class Settings(
    AppSettings,
    db_type,
    CryptSettings,
    FirstUserSettings,
    TestSettings,
    RedisCacheSettings,
    ClientSideCacheSettings,
    RedisQueueSettings,
    RedisRateLimiterSettings,
    DefaultRateLimitSettings,
    EnvironmentSettings,
    AISettings,
    GitHubSettings,
    AccessTokenSettings
):
    pass


settings = Settings()
