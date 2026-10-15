from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr

client_bp = APIRouter(prefix='/api/v1/client', tags=['clients'])

users_db = []


class RegisterModel(BaseModel):
    fio: str
    email: EmailStr
    password: str


class LoginModel(BaseModel):
    email: EmailStr
    password: str


@client_bp.post('/register', status_code=status.HTTP_201_CREATED)
def register(data: RegisterModel):
    for user in users_db:
        if user['email'] == data.email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Пользователь с такой почтой уже существует"
            )

    new_user = {
        "id": len(users_db) + 1,
        "fio": data.fio,
        "email": data.email,
        "password": data.password
    }
    users_db.append(new_user)

    return {
        "message": "Аккаунт успешно создан",
        "user": {
            "id": new_user["id"],
            "fio": new_user["fio"],
            "email": new_user["email"]
        }
    }


@client_bp.post('/login')
def login(data: LoginModel):
    for user in users_db:
        if user['email'] == data.email and user['password'] == data.password:
            return {"message": "Авторизация успешна", "user_id": user['id']}

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Неверная почта или пароль"
    )