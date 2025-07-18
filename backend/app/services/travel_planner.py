
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from app.models.trip import Trip, TravelRecommendation, DailyPlan
from app.models.conversation import UserPreference
from app.utils.config import get_settings

settings = get_settings()


class TravelPlannerService:
    """
    Seyahat planları oluşturan ve öneri veren servis
    """

    def __init__(self, db: Session):
        self.db = db
        self.google_places_api_key = settings.GOOGLE_PLACES_API_KEY
        self.weather_api_key = settings.WEATHER_API_KEY

        # Kategori tanımları
        self.categories = {
            "morning": ["tourist_attraction", "museum", "park", "landmark"],
            "lunch": ["restaurant", "cafe", "food"],
            "afternoon": ["shopping_mall", "market", "cultural_center", "gallery"],
            "dinner": ["restaurant", "local_cuisine", "fine_dining"],
            "evening": ["bar", "nightclub", "theater", "entertainment"]
        }

    async def generate_travel_plan(
            self,
            user_id: str,
            destination: str,
            days: int,
            start_date: Optional[datetime] = None,
            preferences: Optional[Dict] = None
    ) -> Dict:
        """
        Kapsamlı seyahat planı oluşturur
        """
        try:
            # Kullanıcı tercihlerini al
            user_prefs = await self._get_user_preferences(user_id)

            # Hava durumu bilgilerini al
            weather_forecast = await self._get_weather_forecast(destination, days)

            # Genel destinasyon bilgilerini al
            destination_info = await self._get_destination_info(destination)

            # Ana plan objesi
            travel_plan = {
                "destination": destination,
                "days": days,
                "start_date": start_date.isoformat() if start_date else None,
                "weather_forecast": weather_forecast,
                "general_info": destination_info,
                "daily_plans": [],
                "summary": {
                    "total_recommendations": 0,
                    "categories_covered": [],
                    "estimated_budget": 0
                }
            }

            # Her gün için plan oluştur
            for day in range(1, days + 1):
                daily_plan = await self._create_daily_plan(
                    destination,
                    day,
                    user_prefs,
                    weather_forecast.get(f"day_{day}", {})
                )
                travel_plan["daily_plans"].append(daily_plan)
                travel_plan["summary"]["total_recommendations"] += len(daily_plan["recommendations"])

            return {
                "status": "success",
                "plan": travel_plan,
                "message": f"{destination} için {days} günlük planınız hazır!"
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Plan oluşturulurken hata: {str(e)}"
            }

    async def _create_daily_plan(
            self,
            destination: str,
            day: int,
            user_preferences: Dict,
            weather_info: Dict
    ) -> Dict:
        """
        Günlük detay plan oluşturur
        """
        daily_plan = {
            "day": day,
            "weather": weather_info,
            "time_slots": {},
            "recommendations": [],
            "notes": []
        }

        # Hava durumuna göre notlar ekle
        if weather_info.get("precipitation_chance", 0) > 70:
            daily_plan["notes"].append("☔ Yağmur ihtimali yüksek, kapalı mekan aktiviteleri önerilir")

        if weather_info.get("temperature_max", 20) > 30:
            daily_plan["notes"].append("🌡️ Hava sıcak, gölgeli yerler ve bol su tüketimi önerilir")

        # Her zaman dilimi için öneriler al
        time_slots = ["morning", "lunch", "afternoon", "dinner", "evening"]

        for time_slot in time_slots:
            recommendations = await self._get_recommendations_for_time_slot(
                destination,
                time_slot,
                user_preferences,
                weather_info
            )

            daily_plan["time_slots"][time_slot] = {
                "recommendations": recommendations,
                "suggested_time": self._get_suggested_time(time_slot),
                "duration": self._get_estimated_duration(time_slot)
            }

            daily_plan["recommendations"].extend(recommendations)

        return daily_plan

    async def _get_recommendations_for_time_slot(
            self,
            destination: str,
            time_slot: str,
            user_preferences: Dict,
            weather_info: Dict
    ) -> List[Dict]:
        """
        Belirli zaman dilimi için öneriler getirir
        """
        recommendations = []
        categories = self.categories.get(time_slot, ["tourist_attraction"])

        for category in categories[:2]:  # Her zaman dilimi için max 2 kategori
            try:
                places = await self._fetch_places_from_google(destination, category)

                # Kullanıcı tercihleri ve hava durumuna göre filtrele
                filtered_places = self._filter_recommendations(
                    places,
                    user_preferences,
                    weather_info,
                    time_slot
                )

                recommendations.extend(filtered_places[:2])  # Her kategoriden max 2 öneri

            except Exception as e:
                print(f"Kategori {category} için öneri alınırken hata: {e}")
                continue

        return recommendations

    async def _fetch_places_from_google(self, destination: str, category: str) -> List[Dict]:
        """
        Google Places API'den yer önerilerini getirir
        """
        url = "https://maps.googleapis.com/maps/api/place/textsearch/json"

        # Kategori bazlı arama sorguları
        query_map = {
            "restaurant": f"best restaurants in {destination}",
            "tourist_attraction": f"top attractions in {destination}",
            "museum": f"museums in {destination}",
            "park": f"parks in {destination}",
            "shopping_mall": f"shopping in {destination}",
            "bar": f"bars nightlife in {destination}",
            "cafe": f"cafes in {destination}"
        }

        params = {
            "query": query_map.get(category, f"{category} in {destination}"),
            "key": self.google_places_api_key,
            "language": "tr",
            "region": "tr"
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            data = response.json()

            places = []
            for place in data.get("results", [])[:5]:  # İlk 5 sonucu al
                place_info = {
                    "google_place_id": place.get("place_id"),
                    "name": place.get("name"),
                    "category": category,
                    "rating": place.get("rating", 0),
                    "price_level": place.get("price_level", 0),
                    "address": place.get("formatted_address", ""),
                    "latitude": place.get("geometry", {}).get("location", {}).get("lat"),
                    "longitude": place.get("geometry", {}).get("location", {}).get("lng"),
                    "photos": [photo.get("photo_reference") for photo in place.get("photos", [])[:1]],
                    "opening_hours": place.get("opening_hours", {}).get("open_now"),
                    "types": place.get("types", [])
                }
                places.append(place_info)

            return places

        except Exception as e:
            print(f"Google Places API hatası: {e}")
            return []

    def _filter_recommendations(
            self,
            places: List[Dict],
            user_preferences: Dict,
            weather_info: Dict,
            time_slot: str
    ) -> List[Dict]:
        """
        Önerileri kullanıcı tercihleri ve koşullara göre filtreler
        """
        filtered = []

        for place in places:
            score = 0

            # Rating puanı
            score += place.get("rating", 0) * 10

            # Kullanıcı tercih puanı
            for pref_type, pref_value in user_preferences.items():
                if pref_type == "cuisine" and "restaurant" in place.get("category", ""):
                    if pref_value.lower() in " ".join(place.get("types", [])).lower():
                        score += 20

                elif pref_type == "budget":
                    price_level = place.get("price_level", 2)
                    if pref_value == "budget" and price_level <= 2:
                        score += 15
                    elif pref_value == "luxury" and price_level >= 3:
                        score += 15

            # Hava durumu uyumu
            if weather_info.get("precipitation_chance", 0) > 70:
                # Yağmurlu havada kapalı mekanları tercih et
                if any(t in place.get("types", []) for t in ["museum", "shopping_mall", "restaurant"]):
                    score += 10
            else:
                # Güzel havada açık alanları tercih et
                if any(t in place.get("types", []) for t in ["park", "tourist_attraction", "outdoor"]):
                    score += 10

            # Zaman uyumu
            if time_slot in ["morning", "afternoon"] and place.get("opening_hours"):
                score += 5

            place["ai_score"] = score

            # Minimum puan kontrolü
            if score >= 30:  # Minimum kalite eşiği
                filtered.append(place)

        # Puana göre sırala
        return sorted(filtered, key=lambda x: x["ai_score"], reverse=True)

    async def _get_weather_forecast(self, destination: str, days: int) -> Dict:
        """
        Hava durumu tahminini getirir
        """
        try:
            # OpenWeatherMap API
            url = f"http://api.openweathermap.org/data/2.5/forecast"
            params = {
                "q": destination,
                "appid": self.weather_api_key,
                "units": "metric",
                "lang": "tr"
            }

            response = requests.get(url, params=params, timeout=10)
            data = response.json()

            weather_forecast = {}

            for i in range(min(days, 5)):  # Max 5 günlük tahmin
                day_data = data.get("list", [])[i * 8] if len(data.get("list", [])) > i * 8 else {}

                weather_forecast[f"day_{i + 1}"] = {
                    "date": (datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d"),
                    "temperature_max": day_data.get("main", {}).get("temp_max", 20),
                    "temperature_min": day_data.get("main", {}).get("temp_min", 15),
                    "description": day_data.get("weather", [{}])[0].get("description", ""),
                    "icon": day_data.get("weather", [{}])[0].get("icon", ""),
                    "precipitation_chance": day_data.get("pop", 0) * 100,
                    "humidity": day_data.get("main", {}).get("humidity", 50),
                    "wind_speed": day_data.get("wind", {}).get("speed", 0)
                }

            return weather_forecast

        except Exception as e:
            print(f"Hava durumu API hatası: {e}")
            # Varsayılan hava durumu
            return {f"day_{i + 1}": {
                "temperature_max": 22,
                "temperature_min": 16,
                "description": "Genellikle güzel",
                "precipitation_chance": 20
            } for i in range(days)}

    async def _get_destination_info(self, destination: str) -> Dict:
        """
        Destinasyon hakkında genel bilgileri getirir
        """
        return {
            "destination": destination,
            "country": "Azerbaycan" if "baku" in destination.lower() or "bakü" in destination.lower() else "Bilinmiyor",
            "timezone": "Asia/Baku" if "baku" in destination.lower() else "UTC",
            "currency": "AZN" if "baku" in destination.lower() else "USD",
            "language": "Azerbaycan Türkçesi" if "baku" in destination.lower() else "Yerel Dil",
            "best_time_to_visit": "Nisan-Ekim",
            "emergency_numbers": {
                "police": "102",
                "medical": "103",
                "fire": "101"
            }
        }

    async def _get_user_preferences(self, user_id: str) -> Dict:
        """
        Kullanıcının geçmiş tercihlerini analiz eder
        """
        prefs = self.db.query(UserPreference).filter(
            UserPreference.user_id == user_id
        ).all()

        preferences = {}
        for pref in prefs:
            preferences[pref.preference_type] = pref.preference_value

        # Varsayılan tercihler
        if not preferences:
            preferences = {
                "budget": "mid-range",
                "cuisine": "local",
                "activity_level": "moderate"
            }

        return preferences

    def _get_suggested_time(self, time_slot: str) -> str:
        """
        Zaman dilimi için önerilen saatleri döndürür
        """
        time_suggestions = {
            "morning": "09:00-12:00",
            "lunch": "12:00-14:00",
            "afternoon": "14:00-18:00",
            "dinner": "19:00-21:00",
            "evening": "21:00-23:00"
        }
        return time_suggestions.get(time_slot, "Esnek")

    def _get_estimated_duration(self, time_slot: str) -> int:
        """
        Aktivite süresini dakika cinsinden döndürür
        """
        durations = {
            "morning": 180,  # 3 saat
            "lunch": 120,  # 2 saat
            "afternoon": 240,  # 4 saat
            "dinner": 120,  # 2 saat
            "evening": 120  # 2 saat
        }
        return durations.get(time_slot, 120)