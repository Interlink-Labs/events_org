from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Создаем файл базы данных events.db в папке проекта
SQLALCHEMY_DATABASE_URL = "sqlite:///./events.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Зависимость для FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()