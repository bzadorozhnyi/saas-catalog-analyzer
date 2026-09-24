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


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_nested_delimiter="__", extra="ignore")

    LOGFIRE_TOKEN: str | None = None
    DB: DbSettings
    AI: AiSettings


settings = Settings()
