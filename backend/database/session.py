from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import settings

# Create database engine
# pool_pre_ping ensures stale/disconnected connections are discarded
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=1800,
    pool_timeout=30,
    pool_size=10,
    max_overflow=20,
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)
