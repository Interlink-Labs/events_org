import re
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, field_validator

client_bp = APIRouter(prefix='/api/v1/client', tags=['clients'])

users_db = []

# Простая проверка email без внешнего пакета.
# Покрывает 99% практических случаев: что-то@что-то.домен
EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")


class RegisterModel(BaseModel):
    fio: str
    email: str
    password: str

    @field_validator("fio")
    @classmethod
    def validate_fio(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("ФИО слишком короткое")
        return v

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        v = v.strip().lower()
        if not EMAIL_RE.match(v):
            raise ValueError("Некорректный email")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 5:
            raise ValueError("Пароль должен быть не короче 5 символов")
        return v


class LoginModel(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        v = v.strip().lower()
        if not EMAIL_RE.match(v):
            raise ValueError("Некорректный email")
        return v


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