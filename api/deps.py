from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

# Заглушка — заменить на реальную проверку JWT
async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    # TODO: декодировать токен, вернуть пользователя из БД
    return {"id": 1, "role": "manager"}

def require_manager(user: dict = Depends(get_current_user)) -> dict:
    if user["role"] not in ("manager", "admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав")
    return user