from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from datetime import datetime
from app.utils.database import Base


class User(Base):
    """
    Kullanıcı modeli
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True, index=True, nullable=False)  # External user ID
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    full_name = Column(String)

    # User preferences
    preferred_language = Column(String, default="tr")
    preferred_currency = Column(String, default="USD")
    travel_style = Column(String)  # budget, mid-range, luxury

    # Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime)

    # Settings
    notification_settings = Column(Text)  # JSON string
    privacy_settings = Column(Text)  # JSON string