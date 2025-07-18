import requests
from ..config import settings


class WeatherService:
    def __init__(self):
        self.api_key = settings.OPENWEATHERMAP_API_KEY
        self.base_url = "http://api.openweathermap.org/data/2.5"

    async def get_current_weather(self, city: str):
        """Şu anki hava durumu"""
        try:
            url = f"{self.base_url}/weather"
            params = {
                "q": city,
                "appid": self.api_key,
                "units": "metric",
                "lang": "tr"
            }

            response = requests.get(url, params=params)
            response.raise_for_status()

            data = response.json()
            return {
                "city": city,
                "temperature": data["main"]["temp"],
                "description": data["weather"][0]["description"],
                "humidity": data["main"]["humidity"],
                "wind_speed": data["wind"]["speed"],
                "feels_like": data["main"]["feels_like"]
            }
        except Exception as e:
            return {"error": f"Hava durumu alınamadı: {str(e)}"}


weather_service = WeatherService()
import requests
from ..config import settings


class WeatherService:
    def __init__(self) -> None:
        self.api_key = settings.OPENWEATHERMAP_API_KEY
        self.base_url = "http://api.openweathermap.org/data/2.5"

    async def get_current_weather(self, city: str):
        """Şu anki hava durumu"""
        try:
            if self.api_key == "test-key":
                return {
                    "city": city,
                    "temperature": 22,
                    "description": "güneşli",
                    "humidity": 65,
                    "wind_speed": 3.2,
                    "note": "Test verisi - gerçek API key ekleyin"
                }

            url = f"{self.base_url}/weather"
            params = {
                "q": city,
                "appid": self.api_key,
                "units": "metric",
                "lang": "tr"
            }

            response = requests.get(url, params=params)
            response.raise_for_status()

            data = response.json()
            return {
                "city": city,
                "temperature": data["main"]["temp"],
                "description": data["weather"][0]["description"],
                "humidity": data["main"]["humidity"],
                "wind_speed": data["wind"]["speed"]
            }
        except Exception as e:
            return {"error": f"Hava durumu alınamadı: {str(e)}"}


weather_service = WeatherService()