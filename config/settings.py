from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    BOT_TOKEN: str
    ADMIN_ID: int = 0
    DATABASE_URL: str = "sqlite+aiosqlite:///./talabago.db"
    ANTHROPIC_API_KEY: str = ""
    
    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
