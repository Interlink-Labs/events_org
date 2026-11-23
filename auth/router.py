#pip install pyjwt passlib[bcrypt] python-multipart
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
import models
from database import get_db
from auth.security import get_password_hash, verify_password, create_access_token

router = APIRouter(prefix="/api/v1/auth", tags=["Авторизация"])

class UserRegister(BaseModel):
    fio: str
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

@router.post("/register")
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    # Проверяем, есть ли уже такой пользователь
    existing = db.query(models.User).filter(models.User.email == user_data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email уже занят")
    
    # Создаем нового пользователя с захэшированным паролем
    new_user = models.User(
        fio=user_data.fio,
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        role="client"
    )
    db.add(new_user)
    db.commit()
    return {"ok": True, "msg": "Пользователь зарегистрирован"}

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # В OAuth2 формате поле логина называется username, поэтому передаем туда email
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверная почта или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # Создаем JWT токен
    access_token = create_access_token(data={"sub": user.email, "role": user.role})
    return {"access_token": access_token, "token_type": "bearer"}