from pydantic_settings import BaseSettings, SettingsConfigDict


class DbSettings(BaseSettings):
    HOST: str
    PORT: int
    USER: str
    PASSWORD: str
    NAME: str
    SSL_MODE: str

    @property
    def url(self) -> str:
        base = f"postgresql+asyncpg://{self.USER}:{self.PASSWORD}@{self.HOST}:{self.PORT}/{self.NAME}"
        return f"{base}?ssl={self.SSL_MODE}"


class AiSettings(BaseSettings):
    OPENAI_API_KEY: str
    CLASSIFICATION_MODEL: str = "gpt-4o-mini"
    EMBEDDING_MODEL: str = "text-embedding-3-small"


class WorkerSettings(BaseSettings):
    MAX_ATTEMPTS: int = 3
    LOCK_DURATION_SECONDS: int = 60
    HEARTBEAT_INTERVAL_SECONDS: int = 20


class SqsSettings(BaseSettings):
    QUEUE_NAME: str = "catalog-creation-queue"
    ACCOUNT_ID: str = "000000000000"
    REGION: str = "us-east-1"
    ENDPOINT_URL: str | None = None
    ACCESS_KEY_ID: str | None = None
    SECRET_ACCESS_KEY: str | None = None


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_nested_delimiter="__", extra="ignore")

    LOGFIRE_TOKEN: str | None = None
    DB: DbSettings
    AI: AiSettings
    WORKER: WorkerSettings = WorkerSettings()
    SQS: SqsSettings = SqsSettings()


settings = Settings()
