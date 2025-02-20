from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL =  os.getenv("DATABASEURL")
engine = create_engine( DATABASE_URL, 
                        pool_size=10,  
                        max_overflow=20, 
                        pool_timeout=30,  
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
        