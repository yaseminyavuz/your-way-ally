import os
from pydantic import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """
    Uygulama ayarları
    """

    # Database
    DATABASE_URL: str = "sqlite:///./your_way_ally.db"
    DATABASE_ECHO: bool = False

    # API Keys - .env dosyasından okunacak
    GOOGLE_PLACES_API_KEY: Optional[str] = None
    WEATHER_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None

    # Security
    SECRET_KEY: str = "your-secret-key-here"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"

    # CORS
    BACKEND_CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000"
    ]

    # Application
    APP_NAME: str = "Your Way Ally"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Chatbot Settings
    MAX_CONVERSATION_HISTORY: int = 50
    DEFAULT_FEEDBACK_POINTS: int = 2
    PROMPT_RIGHTS_THRESHOLD: int = 50

    # Travel Planning
    MAX_RECOMMENDATIONS_PER_CATEGORY: int = 3
    DEFAULT_TRIP_DURATION: int = 5
    WEATHER_FORECAST_DAYS: int = 5

    # Rate Limiting
    GOOGLE_API_REQUESTS_PER_MINUTE: int = 60
    WEATHER_API_REQUESTS_PER_MINUTE: int = 60

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """
    Settings instance'ını döndürür
    """
    return settings


# API anahtarlarını kontrol etme fonksiyonu
def validate_api_keys():
    """
    Gerekli API anahtarlarının varlığını kontrol eder
    """
    missing_keys = []

    if not settings.GOOGLE_PLACES_API_KEY:
        missing_keys.append("GOOGLE_PLACES_API_KEY")

    if not settings.WEATHER_API_KEY:
        missing_keys.append("WEATHER_API_KEY")

    if missing_keys:
        print(f"⚠️  Eksik API anahtarları: {', '.join(missing_keys)}")
        print("Lütfen .env dosyasına API anahtarlarını ekleyin.")
        return False

    return True


# Development ortamı için varsayılan değerler
def get_development_config():
    """
    Development ortamı için özel ayarlar
    """
    return {
        "debug": True,
        "reload": True,
        "log_level": "debug",
        "host": "0.0.0.0",
        "port": 8000
    }


# Production ortamı için ayarlar
def get_production_config():
    """
    Production ortamı için özel ayarlar
    """
    return {
        "debug": False,
        "reload": False,
        "log_level": "info",
        "host": "0.0.0.0",
        "port": 8000,
        "workers": 4
    }
