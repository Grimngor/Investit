from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
	SECRET_KEY: str
	ALGORITHM: str = "HS256"
	ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
	FINNHUB_API_KEY: str
	OPENFIGI_API_KEY: str = ""
	DATA_DIR: Path = BASE_DIR / "data"
	BACKEND_CORS_ORIGINS: list[str] = [
		"http://localhost:5173",
		"http://localhost:5174",
		"http://localhost:3000",
		"http://127.0.0.1:5173",
		"http://127.0.0.1:5174",
	]

	# Price caching thresholds
	PRICE_STALE_THRESHOLD_DAYS: int = 3
	PRICE_CACHE_HOURS: int = 24
	METADATA_CACHE_DAYS: int = 30
	ISIN_RESOLUTION_CACHE_DAYS: int = 30

	model_config = SettingsConfigDict(env_file=str(BASE_DIR / ".env"), env_file_encoding="utf-8", case_sensitive=True, extra="ignore")


settings = Settings()
