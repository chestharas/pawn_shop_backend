from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
# from models import Account
from database import get_db
from response_model import ResponseModel
from routes.oauth2.repository import get_current_user
from routes.user.repository import Staff
from routes.user.model import *
# from routes.user.model import CreatePawn 

router = APIRouter(
    tags=["pawn"],
    prefix="/api"
)

staff = Staff()
staff_service = Staff()

""" Manage Pawn and Payment """ 
@router.post("/pawn", response_model = ResponseModel)
def create_pawn(pawn_info: CreatePawn, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    staff.is_staff(current_user)
    return staff.create_pawn(pawn_info, db, current_user)

@router.get("/pawn", response_model=ResponseModel)
def get_pawn_by_id(cus_id: Optional[int] = None, cus_name: Optional[str] = None, phone_number: Optional[str] = None, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    staff.is_staff(current_user)
    return staff.get_client_pawn(db, cus_id, cus_name, phone_number)
