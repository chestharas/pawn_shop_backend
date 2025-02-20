from fastapi import Depends, HTTPException, status, APIRouter
from typing import Optional
from datetime import timedelta
from sqlalchemy.orm import Session
from dotenv import load_dotenv

load_dotenv()

from database import get_db
from routes.oauth2.model import UserToken
from routes.oauth2.repository import *

router = APIRouter(
    tags=["Auth"],
)

@router.post("/create_user")
def create_new_user(
    cus_name: str,
    phone_number: str,
    password: Optional[str] = None,
    db: Session = Depends(get_db)):
    
    existing_user = db.query(Account).filter(Account.phone_number == phone_number).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone Number already registered",
        )
    
    create_user(db=db, cus_name=cus_name, phone_number=phone_number, password=password)
    db.commit()
    
    return {
                'code' : status.HTTP_200_OK,
                'status' : "Success",
                'message' : "User created successfully"
    }
    
@router.post("/sign_in")
def sign_in_for_access_token(form_data: UserToken, db: Session = Depends(get_db)):
    user = db.query(Account).filter(Account.phone_number == form_data.phone_number).first()
    if user and pwd_context.verify(form_data.password, user.password):
        access_token_expires = timedelta(minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")))
        refresh_token_expires = timedelta(days=int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS")))
        access_token = create_token(data={"sub": user.phone_number, "id": user.cus_id, "type": "access_token", "role": user.role}, expires_delta=access_token_expires)
        refresh_token = create_token(data={"sub": user.phone_number, "id": user.cus_id, "type": "refresh_token", "role": user.role}, expires_delta=refresh_token_expires)
        return {
            'code' : status.HTTP_200_OK,
            'status' : "Success",
            'result' : {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}
        }

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

@router.post("/refresh_token")
def refresh_access_token(refresh_token: str, db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = verify_refresh_token(refresh_token, credentials_exception)
    user = db.query(Account).filter(Account.phone_number == payload.get("sub")).first()
    if user:
        access_token_expires = timedelta(minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")))
        access_token = create_token(data={"sub": user.phone_number, "id": user.cus_id, "type": "access_token", "role": user.role}, expires_delta=access_token_expires)
        return {
            'code' : status.HTTP_200_OK,
            'status' : "Success",
            'result' : {"access_token": access_token, "token_type": "bearer"}
        }
    
    raise credentials_exception