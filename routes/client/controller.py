from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
# from models import Account
from database import get_db
from response_model import ResponseModel
from routes.oauth2.repository import get_current_user
from routes.client.repository import Staff
from routes.client.model import *
# from routes.user.model import CreatePawn 

router = APIRouter(
    tags=["Client"],
    prefix="/api"
)

staff = Staff()
staff_service = Staff()

""" Manage Client """
@router.post("/client", response_model=ResponseModel)
def create_client(client_info: CreateClient, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    staff.is_staff(current_user)
    return staff.create_client(client_info, db)

@router.get("/client", response_model=ResponseModel[List[GetClient]])
def get_all_client(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    staff.is_staff(current_user)
    return staff.get_client(db)

@router.get("/client/{phone_number}", response_model=ResponseModel[List[GetClient]])
def get_client_phone(
    phone_number: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    staff.is_staff(current_user)
    return staff.get_client_phone(phone_number, db)
