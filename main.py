import uvicorn
from fastapi import FastAPI

from clients.Testun import client_bp

app = FastAPI()

app.include_router(client_bp)


@app.get('/')
def root():
    return {"message": "API работает. Открой /docs"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)