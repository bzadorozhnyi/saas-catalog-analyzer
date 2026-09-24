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
        return (
            f"postgresql+asyncpg://{self.USER}:{self.PASSWORD}"
            f"@{self.HOST}:{self.PORT}/{self.NAME}?ssl={self.SSL_MODE}"
        )


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_nested_delimiter="__", extra="ignore")

    openai_api_key: str
    classification_model: str = "gpt-4o-mini"
    logfire_token: str | None = None
    db: DbSettings


settings = Settings()
