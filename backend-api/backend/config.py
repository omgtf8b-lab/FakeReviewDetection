from functools import lru_cache
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / '.env', override=False)


class Settings(BaseSettings):
    app_name: str = "API Phát hiện đánh giá sản phẩm giả"
    app_env: str = "development"
    secret_key: str = "change-me"
    access_token_expire_minutes: int = 60
    database_url: str = "sqlite:///./fake_review.db"
    cors_origins: str = "http://localhost:3000,http://localhost:5173,http://127.0.0.1:5173,http://localhost:8080,http://127.0.0.1:8080"
    model_path: str = "ml/models/fake_review_model.joblib"
    model_name: str = "tfidf_svm_calibrated"
    model_version: str = "1.0.0"
    model_metrics_path: str = "ml/models/fake_review_model.json"
    verification_base_url: str = "http://127.0.0.1:8001"
    auto_create_tables: bool = True

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @model_validator(mode="after")
    def validate_security(self):
        if self.app_env.lower() in {"production", "prod"} and (self.secret_key == "change-me" or len(self.secret_key) < 32):
            raise ValueError("SECRET_KEY phải là chuỗi bí mật dài ít nhất 32 ký tự trong production")
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
