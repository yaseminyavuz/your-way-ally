from fastapi import APIRouter
from pydantic import BaseModel

# Router tanımı
router = APIRouter(prefix="/auth", tags=["authentication"])

# Basit Pydantic model
class UserCreate(BaseModel):
    username: str
    email: str
    password: str

@router.get("/test")
async def auth_test():
    """Auth route test"""
    return {"message": "Auth route çalışıyor!", "status": "success"}

@router.post("/register")
async def register(user: UserCreate):
    """Basit kullanıcı kaydı - test için"""
    return {
        "message": "Kullanıcı başarıyla oluşturuldu (test mode)",
        "username": user.username,
        "email": user.email,
        "prompt_credits": 10
    }

@router.post("/login")
async def login():
    """Basit giriş - test için"""
    return {
        "message": "Giriş başarılı (test mode)",
        "access_token": "test-token-123",
        "token_type": "bearer"
    }

@router.get("/me")
async def get_current_user():
    """Test kullanıcı bilgisi"""
    return {
        "id": 1,
        "username": "test-user",
        "email": "test@example.com",
        "prompt_credits": 10,
        "is_active": True
    }
