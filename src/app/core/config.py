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
    # No MAX_ATTEMPTS here — SQS's own RedrivePolicy (maxReceiveCount, see
    # localstack-init/init-sqs.sh) is the sole retry-limit authority. FAILED
    # requests aren't terminal; whether they get another attempt is decided
    # by SQS redelivery or a manual DLQ redrive, not by this app.
    LOCK_DURATION_SECONDS: int = 60
    HEARTBEAT_INTERVAL_SECONDS: int = 20


class QueueSettings(BaseSettings):
    QUEUE_NAME: str
    DLQ_NAME: str


class SqsSettings(BaseSettings):
    ACCOUNT_ID: str = "000000000000"
    REGION: str = "us-east-1"
    ENDPOINT_URL: str | None = None
    ACCESS_KEY_ID: str | None = None
    SECRET_ACCESS_KEY: str | None = None
    CATALOG: QueueSettings = QueueSettings(
        QUEUE_NAME="catalog-creation-queue", DLQ_NAME="catalog-creation-dlq"
    )
    REPORT: QueueSettings = QueueSettings(
        QUEUE_NAME="report-generation-queue", DLQ_NAME="report-generation-dlq"
    )


class S3Settings(BaseSettings):
    BUCKET_NAME: str = "report-documents"
    REGION: str = "us-east-1"
    ENDPOINT_URL: str | None = None
    ACCESS_KEY_ID: str | None = None
    SECRET_ACCESS_KEY: str | None = None


class RedisSettings(BaseSettings):
    HOST: str = "localhost"
    PORT: int = 6379

    @property
    def url(self) -> str:
        return f"redis://{self.HOST}:{self.PORT}"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_nested_delimiter="__", extra="ignore")

    LOGFIRE_TOKEN: str | None = None
    OTEL_EXPORTER_OTLP_ENDPOINT: str | None = None
    DB: DbSettings
    AI: AiSettings
    WORKER: WorkerSettings = WorkerSettings()
    SQS: SqsSettings = SqsSettings()
    S3: S3Settings = S3Settings()
    REDIS: RedisSettings = RedisSettings()


settings = Settings()
