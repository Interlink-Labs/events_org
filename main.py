from fastapi import FastAPI, Response, Cookie
from pydantic import BaseModel
import clients
from hashlib import sha256
from random import randint
import traceback



class Package(BaseModel):
    username: str
    password: str


app = FastAPI()

@app.post("/api/v1/clients/reg")
def reg_client(user: Package):
    try:
        username = user.username
        password = user.password
        
        if clients.write_user(username, password):
            return 'пользователь успешно зарегистрирован!'
        else:
            return 'юзернейм занят'
    except Exception as e:
        print(traceback.TracebackException.from_exception(e).format())

@app.post("/api/v1/clients/sign-in")
def sign_client(user: Package):
    try:
        username = user.username
        password = user.password
        
        if clients.validate_user(username, password):
            return 'Вы вошли!'
        else:
            return 'Неверный логин или пароль'
    except Exception as e:
        print(traceback.TracebackException.from_exception(e).format())

@app.post("/api/v1/clients/get")
def get_client(username: str):
    try:
        return clients.get_user(username)
    except Exception as e:
        print(traceback.TracebackException.from_exception(e).format())

@app.post("/api/v1/clients/update")
def update_client(user: Package):
    try:
        username = user.username
        new_password = user.password
        
        if clients.update_user(username, new_password):
            return 'Данные обновлены!'
        else:
            return 'Пользователь не найден'
    except Exception as e:
        print(traceback.TracebackException.from_exception(e).format())

@app.post("/api/v1/clients/delete")
def delete_client(username: str):
    try:
        if clients.delete_user(username):
            return 'Пользователь удален'
        else:
            return 'Пользователь не найден'
    except Exception as e:
        print(traceback.TracebackException.from_exception(e).format())

@app.get("/api/v1/set-cookie")
def set_cookie(username, response: Response):
    try:
        value = str(randint(1, 1000000000))
        access_token = clients.hash_string(value)
        response.set_cookie(
            key="access_token", 
            value=value, 
            httponly=True,
            max_age=900,
            samesite="lax"
        )

        value = str(randint(1, 1000000000))
        refresh_token = clients.hash_string(value)
        response.set_cookie(
            key="refresh_token", 
            value=value, 
            httponly=True,
            max_age=86400,
            samesite="lax"
        )

        clients.write_cookie(access_token, refresh_token, username)
        return {"message": "Куки успешно установлены!"}
    except Exception as e:
        print(traceback.TracebackException.from_exception(e).format())

@app.get('/api/v1/check-cookie')
def check_cookie(username, access_token: str = Cookie('1'), refresh_token: str = Cookie('1')):
    try:
        return clients.get_tokens(username, access_token, refresh_token)
    except Exception as e:
        print(traceback.TracebackException.from_exception(e).format())