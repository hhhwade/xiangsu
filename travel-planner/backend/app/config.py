from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    app_name: str = '行迹智能旅行路线 API'
    environment: str = 'development'
    amap_web_service_key: str | None = None
    cors_origins: str = 'http://localhost:5173'
    redis_url: str | None = None
    request_timeout_seconds: float = 8.0
    planning_cache_ttl_seconds: int = 900
    max_candidate_pool: int = 36

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(',') if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
