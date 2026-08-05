from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Global application configuration.

    Every configuration value comes from the .env file.
    """

    APP_NAME: str = "DevGuardian AI"
    APP_ENV: str = "development"
    DEBUG: bool = True

    DATABASE_URL: str = ""
    SYNC_DATABASE_URL: str = ""

    GITHUB_TOKEN: str = ""
    GITHUB_WEBHOOK_SECRET: str = ""

    GOOGLE_API_KEY: str = ""

    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
    )


settings = Settings()