from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import json

app = FastAPI(title="Your Way Ally - Travel Planner")

# CORS için gerekli (frontend ile backend haberleşmesi için)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatMessage(BaseModel):
    message: str
    user_id: Optional[str] = "default_user"


# Örnek seyahat planları database'i (basit bir dictionary)
travel_plans = {
    "baku_5_days": {
        "destination": "Bakü",
        "days": 5,
        "plan": {
            "day_1": {
                "title": "Varış ve Şehir Merkezi",
                "morning": "✈️ Heydar Aliyev Havalimanı'na varış",
                "afternoon": "🏛️ İçerişehir (Old City) gezisi",
                "evening": "🍽️ Shirvanshah Museum Restaurant'ta akşam yemeği",
                "highlights": ["Maiden Tower", "Palace of Shirvanshahs"]
            },
            "day_2": {
                "title": "Modern Bakü",
                "morning": "🔥 Flame Towers ziyareti",
                "afternoon": "🎨 Heydar Aliyev Center",
                "evening": "🌊 Bakü Bulvarı'nda yürüyüş",
                "highlights": ["Flame Towers", "Heydar Aliyev Center", "Caspian Sea"]
            },
            "day_3": {
                "title": "Kültür ve Sanat",
                "morning": "🖼️ Azerbaycan Halı Müzesi",
                "afternoon": "🎭 Nizami Edebiyat Müzesi",
                "evening": "🍽️ Chinar Restaurant'ta Azerbaycan mutfağı",
                "highlights": ["Traditional crafts", "Local culture", "Azerbaijani cuisine"]
            },
            "day_4": {
                "title": "Yanardag ve Ateshgah",
                "morning": "🔥 Yanardag (Burning Mountain)",
                "afternoon": "🕌 Ateshgah Fire Temple",
                "evening": "🛍️ Nizami Street'te alışveriş",
                "highlights": ["Natural fire phenomena", "Zoroastrian history"]
            },
            "day_5": {
                "title": "Ayrılış",
                "morning": "☕ Kahvaltı ve last minute alışveriş",
                "afternoon": "✈️ Havalimanına transfer",
                "evening": "🛫 Uçuş",
                "highlights": ["Souvenirs", "Airport transfer"]
            }
        },
        "budget": {
            "accommodation": "50-100 USD/gece",
            "food": "20-40 USD/gün",
            "transport": "10-20 USD/gün",
            "activities": "15-30 USD/gün"
        },
        "tips": [
            "Azerbaycan Manatı (AZN) kullanılır",
            "Türkçe konuşanlar için kolay iletişim",
            "Hava genellikle güzel, hafif rüzgarlı",
            "Metro sistemi çok gelişmiş"
        ]
    },
    "istanbul_3_days": {
        "destination": "İstanbul",
        "days": 3,
        "plan": {
            "day_1": {
                "title": "Tarihi Yarımada",
                "morning": "🕌 Ayasofya ve Sultanahmet Camii",
                "afternoon": "🏰 Topkapı Sarayı",
                "evening": "🍽️ Pandeli Restaurant'ta Osmanlı mutfağı",
                "highlights": ["Byzantine architecture", "Ottoman history"]
            },
            "day_2": {
                "title": "Boğaz ve Galata",
                "morning": "🌊 Boğaz turu",
                "afternoon": "🗼 Galata Kulesi",
                "evening": "🍽️ Galata'da balık lokantası",
                "highlights": ["Bosphorus views", "Galata Tower panorama"]
            },
            "day_3": {
                "title": "Kapalıçarşı ve Modern İstanbul",
                "morning": "🛍️ Kapalıçarşı alışverişi",
                "afternoon": "🍽️ Eminönü'nde balık ekmek",
                "evening": "🌃 Taksim'de gece hayatı",
                "highlights": ["Traditional shopping", "Street food", "Modern nightlife"]
            }
        },
        "budget": {
            "accommodation": "30-80 USD/gece",
            "food": "15-35 USD/gün",
            "transport": "5-15 USD/gün",
            "activities": "10-25 USD/gün"
        },
        "tips": [
            "İstanbulkart alın (ulaşım için)",
            "Çay kültürü çok gelişmiş",
            "Pazarlık yapabilirsiniz",
            "Metro ve vapur kullanın"
        ]
    }
}


@app.get("/")
def home():
    return {
        "message": "Your Way Ally - AI Travel Planner 🌍",
        "status": "active",
        "features": ["Chatbot", "Travel Plans", "Smart Recommendations"]
    }


@app.post("/chat")
def chat(data: ChatMessage):
    msg = data.message.lower()

    # Bakü planı
    if "bakü" in msg and any(day in msg for day in ["5", "beş"]):
        plan = travel_plans["baku_5_days"]
        response = f"""🇦🇿 **{plan['destination']} - {plan['days']} Günlük Plan Hazır!**

📅 **Günlük Program:**
🔸 **1. Gün:** {plan['plan']['day_1']['title']}
🔸 **2. Gün:** {plan['plan']['day_2']['title']}  
🔸 **3. Gün:** {plan['plan']['day_3']['title']}
🔸 **4. Gün:** {plan['plan']['day_4']['title']}
🔸 **5. Gün:** {plan['plan']['day_5']['title']}

💰 **Bütçe Rehberi:**
• Konaklama: {plan['budget']['accommodation']}
• Yemek: {plan['budget']['food']}
• Ulaşım: {plan['budget']['transport']}

✨ **İpuçları:** {', '.join(plan['tips'][:2])}

Detayları görmek için '/plan/baku_5_days' endpoint'ini kullanın!"""

        return {
            "response": response,
            "plan_id": "baku_5_days",
            "has_detailed_plan": True
        }

    # İstanbul planı
    elif "istanbul" in msg and any(day in msg for day in ["3", "üç"]):
        plan = travel_plans["istanbul_3_days"]
        response = f"""🇹🇷 **{plan['destination']} - {plan['days']} Günlük Plan Hazır!**

📅 **Günlük Program:**
🔸 **1. Gün:** {plan['plan']['day_1']['title']}
🔸 **2. Gün:** {plan['plan']['day_2']['title']}
🔸 **3. Gün:** {plan['plan']['day_3']['title']}

💰 **Bütçe Rehberi:**
• Konaklama: {plan['budget']['accommodation']}
• Yemek: {plan['budget']['food']}

✨ **İpuçları:** {', '.join(plan['tips'][:2])}

Detayları görmek için '/plan/istanbul_3_days' endpoint'ini kullanın!"""

        return {
            "response": response,
            "plan_id": "istanbul_3_days",
            "has_detailed_plan": True
        }

    # Genel yanıtlar
    elif "merhaba" in msg or "selam" in msg:
        response = """Merhaba! 👋 Size harika seyahat planları hazırlayabilirim!

🌟 **Hazır Planlarım:**
• "Bakü'ye 5 gün gitmek istiyorum"
• "İstanbul'da 3 gün kalacağım"

✨ **Yapabileceklerim:**
📋 Detaylı günlük program
💰 Bütçe rehberi  
🎯 Özel öneriler
🗺️ Rotalar

Hangi şehre seyahat etmek istiyorsunuz?"""

    elif "plan" in msg or "program" in msg:
        response = """📋 **Mevcut Seyahat Planlarım:**

🇦🇿 **Bakü (5 gün)** - Modern şehir + tarih
🇹🇷 **İstanbul (3 gün)** - İki kıta arası macera

💡 **Örnek:** "Bakü'ye 5 gün gitmek istiyorum" yazın!

Hangi destinasyon ilginizi çekiyor?"""

    elif "teşekkür" in msg:
        response = "Rica ederim! 😊 İyi seyahatler dilerim! ✈️"

    else:
        response = """Henüz bu destinasyon için planım yok 😅

🌟 **Mevcut Destinasyonlarım:**
🇦🇿 Bakü (5 gün)
🇹🇷 İstanbul (3 gün)

💡 **Örnek mesaj:** "Bakü'ye 5 gün gitmek istiyorum"

Başka bir destinasyon önerebilirim!"""

    return {"response": response}


@app.get("/plan/{plan_id}")
def get_detailed_plan(plan_id: str):
    """Detaylı seyahat planını getirir"""
    if plan_id in travel_plans:
        return {
            "status": "success",
            "plan": travel_plans[plan_id]
        }
    else:
        return {
            "status": "error",
            "message": "Plan bulunamadı"
        }


@app.get("/plans")
def get_all_plans():
    """Tüm mevcut planları listeler"""
    plans_summary = []
    for plan_id, plan_data in travel_plans.items():
        plans_summary.append({
            "id": plan_id,
            "destination": plan_data["destination"],
            "days": plan_data["days"],
            "title": f"{plan_data['destination']} - {plan_data['days']} Gün"
        })

    return {
        "status": "success",
        "plans": plans_summary
    }


if __name__ == "__main__":
    import uvicorn

    print("🚀 Your Way Ally Travel Planner başlatılıyor...")
    print("🌍 http://localhost:8080")
    print("📚 API Docs: http://localhost:8080/docs")
    uvicorn.run(app, host="127.0.0.1", port=8080)
