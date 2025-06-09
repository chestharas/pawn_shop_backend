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
    tags=["Product"],
    prefix="/api"
)

staff = Staff()
staff_service = Staff()

""" Manage Product """
@router.post("/product", response_model = ResponseModel)
def create_product(product_info: CreateProduct, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    staff.is_staff(current_user)
    return staff.create_product(product_info, db, current_user)

@router.get("/product", response_model=ResponseModel)
def get_all_product(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    staff.is_staff(current_user)
    return staff.get_product(db=db)
