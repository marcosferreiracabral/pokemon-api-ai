import os
import redis
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# --- Configuração ---
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
POOL_SIZE = int(os.getenv("DB_POOL_SIZE", 20))
MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", 10))

# --- Configuração do banco de dados (Pool de Conexões) ---
def get_db_url():
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "postgres")
    host = os.getenv("POSTGRES_HOST", "db")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "pokedex")
    return f"postgresql://{user}:{password}@{host}:{port}/{db}"

engine = create_engine(
    get_db_url(),
    pool_size=POOL_SIZE,
    max_overflow=MAX_OVERFLOW,
    pool_timeout=30,  # 30 segundos para obter uma conexão.
    pool_pre_ping=True # Verifique a disponibilidade da conexão.
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Configuração do Redis ---
try:
    redis_client = redis.Redis(host=REDIS_HOST, port=6379, db=0, decode_responses=True, socket_timeout=2)
except Exception:
    redis_client = None # Recurso alternativo caso o Redis esteja inativo.
