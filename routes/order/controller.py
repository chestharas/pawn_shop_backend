from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import get_db
from response_model import ResponseModel
from routes.oauth2.repository import get_current_user
from routes.order.repository import Staff
from routes.order.model import *

router = APIRouter(
    tags=["Order"],
    prefix="/api"
)

staff = Staff()
staff_service = Staff()

""" Order and Payment """
# @router.get("/order/client_phone", response_model=ResponseModel)
# def get_order_account(
#     phone_number: str,
#     db: Session = Depends(get_db),
#     current_user: dict = Depends(get_current_user)
# ):
#     staff.is_staff(current_user)  # Ensure only staff can access this
#     customer_details = staff.get_order_account(db, phone_number)

#     if not customer_details:
#         raise HTTPException(status_code=404, detail="Customer not found")

#     return ResponseModel(
#         code=200,
#         status="Success",
#         result=customer_details
#     )

@router.post("/order", response_model = ResponseModel)
def create_order(order_info: CreateOrder, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    staff.is_staff(current_user)
    return staff.create_order(order_info, db, current_user)

@router.get("/order", response_model=ResponseModel)
def get_client_order(
    phone_number: Optional[str] = None,
    cus_name: Optional[str] = None,
    cus_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    staff.is_staff(current_user)
    return staff.get_client_order(db, phone_number, cus_name, cus_id)
