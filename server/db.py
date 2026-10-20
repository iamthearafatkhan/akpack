from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

DB_URL = os.getenv("AKP_DB_URL", "sqlite:///./akpack.db")

if DB_URL.startswith("sqlite"):
    engine = create_engine(
        DB_URL, connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(
        DB_URL,
        pool_pre_ping=True,
        pool_recycle=300,
        pool_size=5,
        max_overflow=10,
    )

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()