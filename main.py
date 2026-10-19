from fastapi import FastAPI, Response
from pydantic import BaseModel
import clients
from hashlib import sha256
from random import randint



class Package(BaseModel):
    username: str
    password: str


app = FastAPI()

@app.post("/api/v1/clients/reg")
def reg_client(user: Package):
    username = user.username
    password = user.password
    
    if clients.write_user(username, password):
        return 'пользователь успешно зарегистрирован'
    else:
        return 'юзернейм занят'

@app.post("/api/v1/clients/sign-in")
def sign_client(user: Package):
    username = user.username
    password = user.password
    
    if clients.validate_user(username, password):
        return 'Вы вошли!'
    else:
        return 'Неверный логин или пароль'

@app.post("/api/v1/clients/get")
def get_client(username: str):  
    return clients.get_user(username)

@app.post("/api/v1/clients/update")
def update_client(user: Package):
    username = user.username
    new_password = user.password
    
    if clients.update_user(username, new_password):
        return 'Данные обновлены!'
    else:
        return 'Пользователь не найден'

@app.post("/api/v1/clients/delete")
def delete_client(username: str):
    if clients.delete_user(username):
        return 'Пользователь удален'
    else:
        return 'Пользователь не найден'

@app.get("/api/v1/set-cookie")
def set_cookie(username, response: Response):
    value = str(randint(1, 1000000000))
    access_token = sha256(value.encode('utf-8')).hexdigest()
    response.set_cookie(
        key="access_token", 
        value=value, 
        httponly=True,  # Защита: JavaScript на клиенте не сможет прочитать эту куку
        max_age=900,    # Время жизни куки в секундах (1 час)
        samesite="lax"  # Защита от CSRF-атак
    )

    value = str(randint(1, 1000000000))
    refresh_token = sha256(value.encode('utf-8')).hexdigest()
    response.set_cookie(
        key="refresh_token", 
        value=value, 
        httponly=True,  # Защита: JavaScript на клиенте не сможет прочитать эту куку
        max_age=900,    # Время жизни куки в секундах (1 час)
        samesite="lax"  # Защита от CSRF-атак
    )

    clients.write_cookie(access_token, refresh_token, username)
    return {"message": "Куки успешно установлены!"}