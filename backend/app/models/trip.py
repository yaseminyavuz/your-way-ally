from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, JSON, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class Trip(Base):
    """
    Seyahat planlarını tutar
    """
    __tablename__ = "trips"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, nullable=False, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=True)
    destination = Column(String, nullable=False)
    destination_country = Column(String)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    days = Column(Integer, nullable=False)
    budget = Column(Float, nullable=True)
    currency = Column(String, default="USD")
    traveler_count = Column(Integer, default=1)
    travel_style = Column(String)  # budget, mid-range, luxury

    # Plan detayları
    daily_plans = Column(JSON)  # Her günün detaylı planı
    weather_info = Column(JSON)  # Hava durumu bilgileri
    general_info = Column(JSON)  # Genel destinasyon bilgileri

    # AI önerileri
    recommended_places = Column(JSON)
    recommended_restaurants = Column(JSON)
    recommended_activities = Column(JSON)

    # Durum
    status = Column(String, default="draft")  # draft, confirmed, completed
    is_public = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # İlişkiler
    conversation = relationship("Conversation", backref="trips")


class TravelRecommendation(Base):
    """
    Seyahat önerilerini tutar
    """
    __tablename__ = "travel_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id"), nullable=False)
    google_place_id = Column(String)  # Google Places API'den gelen ID
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)  # restaurant, attraction, hotel, etc.
    subcategory = Column(String)  # italian_restaurant, museum, boutique_hotel, etc.
    description = Column(Text)
    rating = Column(Float)
    price_level = Column(Integer)  # 1-4 arası (Google'dan)
    address = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)

    # Planlama bilgileri
    recommended_day = Column(Integer)
    recommended_time_slot = Column(String)  # morning, afternoon, evening, night
    estimated_duration = Column(Integer)  # dakika cinsinden

    # AI puanlama
    ai_score = Column(Float, default=0.0)  # AI'nin verdiği uygunluk puanı
    user_feedback_avg = Column(Float, default=0.0)  # Kullanıcı feedback ortalaması
    popularity_score = Column(Float, default=0.0)  # Genel popülerlik

    # Metadata
    source = Column(String, default="google_places")  # google_places, manual, tripadvisor, etc.
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # İlişkiler
    trip = relationship("Trip", backref="recommendations")


class DailyPlan(Base):
    """
    Günlük seyahat planlarını detaylı tutar
    """
    __tablename__ = "daily_plans"

    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id"), nullable=False)
    day_number = Column(Integer, nullable=False)
    date = Column(DateTime)

    # Hava durumu
    weather_condition = Column(String)
    temperature_max = Column(Float)
    temperature_min = Column(Float)
    precipitation_chance = Column(Integer)

    # Zaman dilimi planları
    morning_plan = Column(JSON)  # 06:00-12:00
    afternoon_plan = Column(JSON)  # 12:00-18:00
    evening_plan = Column(JSON)  # 18:00-24:00

    # Notlar ve özel durumlar
    notes = Column(Text)
    special_events = Column(JSON)  # Festivaller, etkinlikler
    transportation = Column(JSON)  # Ulaşım planları

    # Durum
    is_completed = Column(Boolean, default=False)
    completion_feedback = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # İlişkiler
    trip = relationship("Trip", backref="daily_plans_detailed")