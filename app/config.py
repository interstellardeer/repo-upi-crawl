from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    BASE_URL: str = "https://repository.upi.edu"
    DB_PATH: str = "data/upi_repository.db"
    CONCURRENCY: int = 5
    REQUEST_DELAY: float = 0.5
    CRAWL_API_KEY: str = "changeme"


settings = Settings()
