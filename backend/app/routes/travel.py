from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime
from sqlalchemy.orm import Session
from app.utils.database import get_db
from app.services.travel_planner import TravelPlannerService
from app.services.chatbot_service import ChatbotService

router = APIRouter(prefix="/travel", tags=["travel"])


# Request Models
class TravelPlanRequest(BaseModel):
    user_id: str
    destination: str
    days: int
    start_date: Optional[datetime] = None
    budget: Optional[float] = None
    traveler_count: Optional[int] = 1
    preferences: Optional[Dict] = None


class ChatRequest(BaseModel):
    user_id: str
    message: str
    conversation_id: Optional[int] = None


class FeedbackRequest(BaseModel):
    conversation_id: int
    recommendation_id: str
    recommendation_name: str
    recommendation_type: str
    rating: int  # 1-5 arası
    comment: Optional[str] = None
    day_number: Optional[int] = None
    time_slot: Optional[str] = None


# Travel Plan Endpoints
@router.post("/plan")
async def create_travel_plan(
        request: TravelPlanRequest,
        db: Session = Depends(get_db)
):
    """
    Yeni seyahat planı oluşturur
    """
    try:
        planner = TravelPlannerService(db)

        result = await planner.generate_travel_plan(
            user_id=request.user_id,
            destination=request.destination,
            days=request.days,
            start_date=request.start_date,
            preferences=request.preferences or {}
        )

        return {
            "status": "success",
            "data": result,
            "message": f"{request.destination} için {request.days} günlük planınız hazır!"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Plan oluşturulurken hata: {str(e)}")


@router.get("/plan/{conversation_id}")
async def get_travel_plan(
        conversation_id: int,
        user_id: str,
        db: Session = Depends(get_db)
):
    """
    Mevcut seyahat planını getirir
    """
    try:
        from app.models.conversation import Conversation

        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id
        ).first()

        if not conversation:
            raise HTTPException(status_code=404, detail="Konuşma bulunamadı")

        if not conversation.travel_plan:
            raise HTTPException(status_code=404, detail="Bu konuşmada henüz bir plan oluşturulmamış")

        return {
            "status": "success",
            "data": {
                "conversation_id": conversation.id,
                "destination": conversation.destination,
                "days": conversation.days,
                "travel_plan": conversation.travel_plan,
                "created_at": conversation.created_at
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Plan getirilirken hata: {str(e)}")


# Chatbot Endpoints
@router.post("/chat")
async def chat_with_bot(
        request: ChatRequest,
        db: Session = Depends(get_db)
):
    """
    Chatbot ile konuşma
    """
    try:
        chatbot = ChatbotService(db)

        result = await chatbot.process_message(
            user_id=request.user_id,
            message=request.message,
            conversation_id=request.conversation_id
        )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chatbot hatası: {str(e)}")


@router.post("/feedback")
async def submit_feedback(
        request: FeedbackRequest,
        db: Session = Depends(get_db)
):
    """
    Seyahat önerisi için geri bildirim gönder
    """
    try:
        from app.models.conversation import Conversation, TravelFeedback

        # Konuşmayı kontrol et
        conversation = db.query(Conversation).filter(
            Conversation.id == request.conversation_id
        ).first()

        if not conversation:
            raise HTTPException(status_code=404, detail="Konuşma bulunamadı")

        # Feedback kaydet
        feedback = TravelFeedback(
            conversation_id=request.conversation_id,
            recommendation_id=request.recommendation_id,
            recommendation_type=request.recommendation_type,
            recommendation_name=request.recommendation_name,
            rating=request.rating,
            comment=request.comment,
            day_number=request.day_number,
            time_slot=request.time_slot
        )

        db.add(feedback)

        # Puan hesapla ve ekle
        points_earned = request.rating * 2
        conversation.total_score += points_earned

        # Prompt hakkı kontrolü (her 50 puana 1 hak)
        if conversation.total_score >= 50 and (conversation.total_score - points_earned) < 50:
            conversation.prompt_rights += 1
            prompt_earned = True
        else:
            prompt_earned = False

        db.commit()

        # Kullanıcı tercihlerini güncelle (AI öğrenmesi için)
        await _update_user_preferences(
            conversation.user_id,
            request.recommendation_type,
            request.rating,
            db
        )

        return {
            "status": "success",
            "message": "Geri bildiriminiz alındı!",
            "data": {
                "points_earned": points_earned,
                "total_score": conversation.total_score,
                "prompt_rights": conversation.prompt_rights,
                "prompt_earned": prompt_earned
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Feedback kaydedilirken hata: {str(e)}")


@router.get("/conversation/{conversation_id}/history")
async def get_conversation_history(
        conversation_id: int,
        user_id: str,
        db: Session = Depends(get_db)
):
    """
    Konuşma geçmişini getirir
    """
    try:
        chatbot = ChatbotService(db)
        history = await chatbot.get_conversation_history(conversation_id, user_id)

        return {
            "status": "success",
            "data": {
                "conversation_id": conversation_id,
                "history": history
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Geçmiş getirilirken hata: {str(e)}")


@router.get("/user/{user_id}/stats")
async def get_user_stats(
        user_id: str,
        db: Session = Depends(get_db)
):
    """
    Kullanıcı istatistiklerini getirir
    """
    try:
        chatbot = ChatbotService(db)
        stats = await chatbot.get_user_stats(user_id)

        return {
            "status": "success",
            "data": stats
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"İstatistikler getirilirken hata: {str(e)}")


@router.get("/user/{user_id}/conversations")
async def get_user_conversations(
        user_id: str,
        db: Session = Depends(get_db)
):
    """
    Kullanıcının tüm konuşmalarını getirir
    """
    try:
        from app.models.conversation import Conversation

        conversations = db.query(Conversation).filter(
            Conversation.user_id == user_id
        ).order_by(Conversation.created_at.desc()).all()

        result = []
        for conv in conversations:
            result.append({
                "id": conv.id,
                "destination": conv.destination,
                "days": conv.days,
                "total_score": conv.total_score,
                "prompt_rights": conv.prompt_rights,
                "is_active": conv.is_active,
                "created_at": conv.created_at,
                "has_plan": bool(conv.travel_plan)
            })

        return {
            "status": "success",
            "data": {
                "conversations": result,
                "total_count": len(result)
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Konuşmalar getirilirken hata: {str(e)}")


# Helper Functions
async def _update_user_preferences(
        user_id: str,
        recommendation_type: str,
        rating: int,
        db: Session
):
    """
    Kullanıcı tercihlerini günceller (AI öğrenmesi için)
    """
    try:
        from app.models.conversation import UserPreference

        # Mevcut tercihi ara
        existing_pref = db.query(UserPreference).filter(
            UserPreference.user_id == user_id,
            UserPreference.preference_type == recommendation_type
        ).first()

        if existing_pref:
            # Mevcut tercihi güncelle
            if rating >= 4:
                existing_pref.weight += 1
            elif rating <= 2:
                existing_pref.weight = max(1, existing_pref.weight - 1)
        else:
            # Yeni tercih oluştur
            if rating >= 4:
                new_pref = UserPreference(
                    user_id=user_id,
                    preference_type=recommendation_type,
                    preference_value="liked",
                    weight=1
                )
                db.add(new_pref)

        db.commit()

    except Exception as e:
        print(f"Tercih güncelleme hatası: {e}")


# Destinations and Recommendations
@router.get("/destinations/popular")
async def get_popular_destinations():
    """
    Popüler destinasyonları getirir
    """
    popular_destinations = [
        {
            "name": "Bakü",
            "country": "Azerbaycan",
            "description": "Hazar Denizi kıyısındaki modern şehir",
            "image": "baku.jpg",
            "recommended_days": 5,
            "best_season": "Nisan-Ekim"
        },
        {
            "name": "İstanbul",
            "country": "Türkiye",
            "description": "İki kıtanın buluştuğu tarih şehri",
            "image": "istanbul.jpg",
            "recommended_days": 4,
            "best_season": "Mart-Kasım"
        },
        {
            "name": "Paris",
            "country": "Fransa",
            "description": "Aşk ve sanat şehri",
            "image": "paris.jpg",
            "recommended_days": 6,
            "best_season": "Nisan-Ekim"
        }
    ]

    return {
        "status": "success",
        "data": popular_destinations
    }