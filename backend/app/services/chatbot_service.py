import re
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from app.models.conversation import Conversation, Message, TravelFeedback, UserPreference
from app.models.trip import Trip
from app.services.travel_planner import TravelPlannerService


class ChatbotService:
    """
    Chatbot mantığını yöneten servis
    """

    def __init__(self, db: Session):
        self.db = db
        self.travel_planner = TravelPlannerService(db)

        # Intent tanımlama patterns
        self.intent_patterns = {
            "travel_request": [
                r"(\w+)(\s+için|\s+ye|\s+ya|\s+da|\s+de).*?(\d+)\s*gün",
                r"(\d+)\s*gün.*?(\w+)(\s+seyahat|\s+gitmek|\s+gideceğim)",
                r"(\w+)\s+(\d+)\s*günlük\s*plan"
            ],
            "feedback": [
                r"(beğendim|güzel|harika|mükemmel|süper)",
                r"(beğenmedim|kötü|berbat|hiç iyi değil)",
                r"(\d+)\s*(puan|yıldız|star)"
            ],
            "question": [
                r"(nedir|nasıl|ne zaman|nerede|kim|hangi)",
                r"\?",
                r"(önerir misin|tavsiye|öneri)"
            ],
            "greeting": [
                r"(merhaba|selam|hey|hi|hello)",
                r"(nasılsın|naber|ne var ne yok)"
            ]
        }

    async def process_message(
            self,
            user_id: str,
            message: str,
            conversation_id: Optional[int] = None
    ) -> Dict:
        """
        Kullanıcı mesajını işler ve uygun yanıt üretir
        """
        try:
            # Intent'i tespit et
            intent, entities = self._detect_intent(message)

            # Konuşmayı al veya oluştur
            conversation = await self._get_or_create_conversation(
                user_id, conversation_id, entities
            )

            # Intent'e göre yanıt üret
            response = await self._generate_response(
                intent, entities, conversation, message
            )

            # Mesajı kaydet
            await self._save_message(conversation.id, message, response["message"])

            return {
                "status": "success",
                "conversation_id": conversation.id,
                "intent": intent,
                "response": response["message"],
                "data": response.get("data"),
                "suggestions": response.get("suggestions", [])
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Üzgünüm, bir hata oluştu: {str(e)}",
                "conversation_id": conversation_id
            }

    def _detect_intent(self, message: str) -> Tuple[str, Dict]:
        """
        Mesajdan intent ve entity'leri çıkarır
        """
        message_lower = message.lower()
        entities = {}

        # Seyahat talebi kontrolü
        for pattern in self.intent_patterns["travel_request"]:
            match = re.search(pattern, message_lower)
            if match:
                groups = match.groups()

                # Destinasyon ve gün sayısını çıkar
                for group in groups:
                    if group and group.isdigit():
                        entities["days"] = int(group)
                    elif group and not group.isdigit() and len(group) > 2:
                        # Bağlaç olmayan kelimeleri destinasyon olarak al
                        if group not in ["için", "ye", "ya", "da", "de", "seyahat", "gitmek", "gideceğim", "günlük",
                                         "plan"]:
                            entities["destination"] = group.title()

                if "days" in entities and "destination" in entities:
                    return "travel_request", entities

        # Feedback kontrolü
        for pattern in self.intent_patterns["feedback"]:
            if re.search(pattern, message_lower):
                # Puanlama varsa çıkar
                rating_match = re.search(r"(\d+)\s*(puan|yıldız|star)", message_lower)
                if rating_match:
                    entities["rating"] = int(rating_match.group(1))

                # Pozitif/negatif sentiment
                if any(word in message_lower for word in ["beğendim", "güzel", "harika", "mükemmel", "süper"]):
                    entities["sentiment"] = "positive"
                    if "rating" not in entities:
                        entities["rating"] = 5
                elif any(word in message_lower for word in ["beğenmedim", "kötü", "berbat", "hiç iyi değil"]):
                    entities["sentiment"] = "negative"
                    if "rating" not in entities:
                        entities["rating"] = 1

                return "feedback", entities

        # Soru kontrolü
        for pattern in self.intent_patterns["question"]:
            if re.search(pattern, message_lower):
                return "question", entities

        # Selamlama kontrolü
        for pattern in self.intent_patterns["greeting"]:
            if re.search(pattern, message_lower):
                return "greeting", entities

        # Varsayılan
        return "general", entities

    async def _get_or_create_conversation(
            self,
            user_id: str,
            conversation_id: Optional[int],
            entities: Dict
    ) -> Conversation:
        """
        Konuşmayı alır veya yeni oluşturur
        """
        if conversation_id:
            conversation = self.db.query(Conversation).filter(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id
            ).first()

            if conversation:
                return conversation

        # Yeni konuşma oluştur
        conversation = Conversation(
            user_id=user_id,
            destination=entities.get("destination", ""),
            days=entities.get("days", 0),
            is_active=True
        )

        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)

        return conversation

    async def _generate_response(
            self,
            intent: str,
            entities: Dict,
            conversation: Conversation,
            original_message: str
    ) -> Dict:
        """
        Intent'e göre yanıt üretir
        """
        if intent == "greeting":
            return await self._handle_greeting()

        elif intent == "travel_request":
            return await self._handle_travel_request(entities, conversation)

        elif intent == "feedback":
            return await self._handle_feedback(entities, conversation, original_message)

        elif intent == "question":
            return await self._handle_question(original_message, conversation)

        else:
            return await self._handle_general(original_message, conversation)

    async def _handle_greeting(self) -> Dict:
        """
        Selamlama mesajlarını yanıtlar
        """
        greetings = [
            "Merhaba! Size nasıl yardımcı olabilirim? 🌍",
            "Selam! Hangi şehre seyahat etmek istiyorsunuz? ✈️",
            "Hey! Size harika bir seyahat planı hazırlayabilirim. Nereye gitmek istiyorsunuz?"
        ]

        import random
        return {
            "message": random.choice(greetings),
            "suggestions": [
                "Bakü'ye 5 gün seyahat edeceğim",
                "İstanbul'da 3 günlük plan yap",
                "Paris için öneriler ver"
            ]
        }

    async def _handle_travel_request(self, entities: Dict, conversation: Conversation) -> Dict:
        """
        Seyahat talebi işler
        """
        destination = entities.get("destination")
        days = entities.get("days")

        if not destination or not days:
            return {
                "message": "Hangi şehre kaç gün seyahat etmek istediğinizi belirtir misiniz? Örneğin: 'Bakü'ye 5 gün seyahat edeceğim'",
                "suggestions": [
                    "Bakü'ye 5 gün",
                    "İstanbul'a 3 gün",
                    "Antalya'ya 7 gün"
                ]
            }

        # Konuşmayı güncelle
        conversation.destination = destination
        conversation.days = days
        self.db.commit()

        # Seyahat planı oluştur
        plan_result = await self.travel_planner.generate_travel_plan(
            user_id=conversation.user_id,
            destination=destination,
            days=days,
            start_date=datetime.now() + timedelta(days=7)  # 1 hafta sonra varsayılan
        )

        if plan_result["status"] == "success":
            # Planı konuşmaya kaydet
            conversation.travel_plan = plan_result["plan"]
            self.db.commit()

            return {
                "message": f"Harika! {destination} için {days} günlük seyahat planınızı hazırladım! 🎉\n\nPlanınızda toplam {plan_result['plan']['summary']['total_recommendations']} öneri var. Her öneri için geri bildirimde bulunarak beni eğitebilir ve puan kazanabilirsiniz! 🌟",
                "data": {
                    "travel_plan": plan_result["plan"],
                    "conversation_id": conversation.id
                },
                "suggestions": [
                    "Planı detaylarıyla göster",
                    "1. günü göster",
                    "Restoran önerilerini göster"
                ]
            }
        else:
            return {
                "message": f"Üzgünüm, {destination} için plan oluştururken bir sorun yaşadım. Tekrar deneyebilir misiniz?",
                "suggestions": [
                    "Tekrar dene",
                    "Başka şehir öner",
                    "Yardım"
                ]
            }

    async def _handle_feedback(self, entities: Dict, conversation: Conversation, message: str) -> Dict:
        """
        Geri bildirim işler
        """
        if not conversation.travel_plan:
            return {
                "message": "Geri bildirimde bulunmak için önce bir seyahat planı oluşturmamız gerekiyor. Hangi şehre kaç gün seyahat etmek istiyorsunuz?"
            }

        rating = entities.get("rating", 3)
        sentiment = entities.get("sentiment", "neutral")

        # Basit feedback kaydı (gerçek implementasyonda recommendation_id gerekli)
        feedback = TravelFeedback(
            conversation_id=conversation.id,
            recommendation_id="general_plan",  # Genel plan feedback'i
            recommendation_type="general",
            recommendation_name="Travel Plan",
            rating=rating,
            comment=message
        )

        self.db.add(feedback)

        # Puan hesapla ve ekle
        points_earned = rating * 2  # Her puan için 2 puan
        conversation.total_score += points_earned

        # Prompt hakkı kontrolü
        new_prompt_rights = 0
        if conversation.total_score >= 50 and conversation.total_score % 50 == 0:
            new_prompt_rights = 1
            conversation.prompt_rights += 1

        self.db.commit()

        response_message = f"Geri bildiriminiz için teşekkürler! {points_earned} puan kazandınız. 🎁\n\nToplam puanınız: {conversation.total_score}"

        if new_prompt_rights > 0:
            response_message += f"\n\n🚀 Tebrikler! 50 puana ulaştığınız için bir prompt hakkı kazandınız! Artık istediğiniz özel talebi yapabilirsiniz."

        return {
            "message": response_message,
            "data": {
                "points_earned": points_earned,
                "total_score": conversation.total_score,
                "prompt_rights": conversation.prompt_rights
            },
            "suggestions": [
                "Daha fazla öneri göster",
                "Planın devamını göster",
                "Yeni plan oluştur"
            ]
        }

    async def _handle_question(self, message: str, conversation: Conversation) -> Dict:
        """
        Genel soruları yanıtlar
        """
        message_lower = message.lower()

        # Destinasyon hakkında sorular
        if conversation.destination and any(word in message_lower for word in ["hava", "weather", "sıcaklık"]):
            if conversation.travel_plan and "weather_forecast" in conversation.travel_plan:
                weather_info = conversation.travel_plan["weather_forecast"]
                response = f"{conversation.destination} için hava durumu:\n\n"

                for day, weather in list(weather_info.items())[:3]:
                    response += f"📅 {weather['date']}: {weather['description']}, {weather['temperature_max']}°C\n"

                return {"message": response}

        # Restoran soruları
        elif any(word in message_lower for word in ["restoran", "restaurant", "yemek", "food"]):
            return {
                "message": f"{conversation.destination or 'Bu destinasyon'} için restoran önerilerinizi seyahat planınızda bulabilirsiniz. Hangi gün için restoran önerisi istiyorsunuz?",
                "suggestions": ["1. gün restoranları", "2. gün restoranları", "Tüm restoranları göster"]
            }

        # Genel seyahat soruları
        else:
            return {
                "message": "Bu konuda size daha iyi yardımcı olabilmek için önce bir seyahat planı oluşturalım. Hangi şehre kaç gün seyahat etmek istiyorsunuz?",
                "suggestions": [
                    "Bakü'ye 5 gün",
                    "İstanbul'a 3 gün",
                    "Seyahat tavsiyeleri"
                ]
            }

    async def _handle_general(self, message: str, conversation: Conversation) -> Dict:
        """
        Genel mesajları işler
        """
        responses = [
            "Anlayabilmek için biraz daha detay verebilir misiniz? 🤔",
            "Size nasıl yardımcı olabilirim? Seyahat planı oluşturmak ister misiniz? ✈️",
            "Daha spesifik bir soru sorabilir misiniz? Örneğin hangi şehre seyahat etmek istiyorsunuz? 🌍"
        ]

        import random
        return {
            "message": random.choice(responses),
            "suggestions": [
                "Seyahat planı oluştur",
                "Popüler destinasyonlar",
                "Yardım"
            ]
        }

    async def _save_message(self, conversation_id: int, user_message: str, bot_response: str):
        """
        Mesajı veritabanına kaydeder
        """
        message = Message(
            conversation_id=conversation_id,
            user_message=user_message,
            bot_response=bot_response,
            timestamp=datetime.utcnow()
        )

        self.db.add(message)
        self.db.commit()

    async def get_conversation_history(self, conversation_id: int, user_id: str) -> List[Dict]:
        """
        Konuşma geçmişini getirir
        """
        messages = self.db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.timestamp).all()

        history = []
        for msg in messages:
            history.extend([
                {"type": "user", "message": msg.user_message, "timestamp": msg.timestamp},
                {"type": "bot", "message": msg.bot_response, "timestamp": msg.timestamp}
            ])

        return history

    async def get_user_stats(self, user_id: str) -> Dict:
        """
        Kullanıcı istatistiklerini getirir
        """
        conversations = self.db.query(Conversation).filter(
            Conversation.user_id == user_id
        ).all()

        total_score = sum(conv.total_score for conv in conversations)
        total_prompt_rights = sum(conv.prompt_rights for conv in conversations)
        total_conversations = len(conversations)

        return {
            "total_score": total_score,
            "prompt_rights": total_prompt_rights,
            "conversations_count": total_conversations,
            "level": self._calculate_user_level(total_score)
        }

    def _calculate_user_level(self, total_score: int) -> Dict:
        """
        Kullanıcı seviyesini hesaplar
        """
        levels = [
            {"level": 1, "name": "Yeni Gezgin", "min_score": 0},
            {"level": 2, "name": "Deneyimli Gezgin", "min_score": 100},
            {"level": 3, "name": "Seyahat Uzmanı", "min_score": 300},
            {"level": 4, "name": "Seyahat Gurusu", "min_score": 600},
            {"level": 5, "name": "Dünya Gezgini", "min_score": 1000}
        ]

        current_level = levels[0]
        for level in levels:
            if total_score >= level["min_score"]:
                current_level = level

        return current_level