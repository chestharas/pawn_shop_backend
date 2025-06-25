from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
# from models import Account
from database import get_db
from response_model import ResponseModel
from routes.oauth2.repository import get_current_user
from routes.pawn.repository import Staff
from routes.pawn.model import *
# from routes.user.model import CreatePawn 

router = APIRouter(
    tags=["Pawn"],
    prefix="/api"
)

staff = Staff()
staff_service = Staff()

""" Manage Pawn and Payment """ 
@router.get("/pawn", response_model=ResponseModel)
def get_pawn_by_id(
    db: Session = Depends(get_db), 
    current_user: dict = Depends(get_current_user)
):
    staff.is_staff(current_user)
    result = staff.get_all_pawn_details(db)  # Use the new method
    
    return ResponseModel(
        code=200,
        status="success", 
        message="Pawn details retrieved successfully",
        result=result
    )

@router.post("/pawn", response_model = ResponseModel)
def create_pawn(
    pawn_info: CreatePawn, 
    db: Session = Depends(get_db), 
    current_user: dict = Depends(get_current_user)
):
    staff.is_staff(current_user)
    return staff.create_pawn(pawn_info, db, current_user)

@router.get("/pawn/all_client", response_model=ResponseModel)
def get_all_client_pawn(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    staff.is_staff(current_user)
    return staff.get_all_client_pawn(db)

@router.get("/pawn/client/{cus_id}", response_model=ResponseModel)
def get_client_id(
    cus_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    staff.is_staff(current_user)
    return staff.get_client_id(cus_id, db)

@router.get("/pawn/search", response_model=ResponseModel)
def get_client_pawn(
    phone_number: Optional[str] = None,
    cus_name: Optional[str] = None,
    cus_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    staff.is_staff(current_user)
    return staff.get_client_pawn(db, phone_number, cus_name, cus_id)

@router.get("/pawn/next-id", response_model=ResponseModel)
def get_next_pawn_id(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    staff.is_staff(current_user)
    return staff.get_next_pawn_id(db)

@router.get("/pawn/last", response_model=ResponseModel)
def get_last_pawns(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    staff.is_staff(current_user)
    return staff.get_last_pawns(db)


@router.get("/pawn/print", response_model=ResponseModel)
def get_pawn_by_id(
    pawn_id: Optional[int] = None, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    staff.is_staff(current_user)
    return staff.get_pawn_print(db, pawn_id)