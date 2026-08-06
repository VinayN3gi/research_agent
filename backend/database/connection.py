import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from config import DATABASE_KEY

# Convert neon postgres URL to sqlalchemy format if needed (postgres:// -> postgresql://)
db_url = DATABASE_KEY
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

if not db_url:
    print("WARNING: DATABASE_KEY is not set.")

engine = create_engine(db_url, pool_pre_ping=True) if db_url else None
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
