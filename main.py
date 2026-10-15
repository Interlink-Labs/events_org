from fastapi import FastAPI
from pydantic import BaseModel
import clients


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