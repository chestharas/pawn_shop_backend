from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    # Fallback for development - you should set this in your .env file
    DATABASE_URL = "postgresql://pawnshop:pawnshop123@localhost:5432/pawnshop"
    print("⚠️  WARNING: DATABASE_URL not set. Using fallback URL. Please set DATABASE_URL in your .env file.")

engine = create_engine( DATABASE_URL, 
                        pool_size=50,  
                        max_overflow=60, 
                        pool_timeout=70,  
                        pool_recycle=1800,
                        pool_pre_ping=True
                    )
Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()
        