from fastapi import APIRouter

router = APIRouter(prefix="/weather", tags=["weather"])


@router.get("/{city}")
async def get_weather(city: str):
    """Şehir için hava durumu"""

    return {
        "city": city,
        "temperature": 22,
        "description": "güneşli",
        "humidity": 65,
        "wind_speed": 3.2,
        "feels_like": 25,
        "note": "Test verisi"
    }


@router.get("/forecast/{city}")
async def get_forecast(city: str):
    """5 günlük hava durumu tahmini"""

    forecast = []
    for i in range(5):
        forecast.append({
            "date": f"2025-07-{14 + i}",
            "temperature": 20 + i,
            "description": "parçalı bulutlu"
        })

    return {"city": city, "forecast": forecast}


@router.get("/test")
async def weather_test():
    return {"message": "Weather route çalışıyor!"}
