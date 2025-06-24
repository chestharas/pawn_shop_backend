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
    # phone_number: Optional[str] = None,
    # cus_name: Optional[str] = None,
    # cus_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    staff.is_staff(current_user)
    return staff.get_client_order(db)

# @router.get("/order", response_model=ResponseModel)
# def get_client_order(
#     phone_number: Optional[str] = None,
#     cus_name: Optional[str] = None,
#     cus_id: Optional[int] = None,
#     db: Session = Depends(get_db),
#     current_user: dict = Depends(get_current_user)
# ):
#     staff.is_staff(current_user)
#     return staff.get_client_order(db, phone_number, cus_name, cus_id)

# @router.get("/order", response_model=ResponseModel)
# def get_client_order_info(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
#     staff.is_staff(current_user)
#     return staff.get_customers_with_orders(db)

@router.get("/order/all_client", response_model=ResponseModel)
def get_all_client_order(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    staff.is_staff(current_user)
    return staff.get_all_client_order(db)

@router.get("/order/client/{cus_id}", response_model=ResponseModel)
def get_client_id(
    cus_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    staff.is_staff(current_user)
    return staff.get_client_id(cus_id, db)

@router.get("/order/search", response_model=ResponseModel)
def get_client_order(
    phone_number: Optional[str] = None,
    cus_name: Optional[str] = None,
    cus_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    staff.is_staff(current_user)
    return staff.get_client_order(db, phone_number, cus_name, cus_id)

@router.get("/order/next-id", response_model=ResponseModel)
def get_next_order_id(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    staff.is_staff(current_user)
    return staff.get_next_order_id(db)

@router.get("/order/last", response_model=ResponseModel)
def get_last_order(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    staff.is_staff(current_user)
    return staff.get_last_order(db)

# @router.get("/order/{order_id}/print", response_model=ResponseModel)
# def print_order(
#     order_id: int,
#     db: Session = Depends(get_db),
#     current_user: dict = Depends(get_current_user)
# ):
#     staff.is_staff(current_user)
#     return staff.print_order(order_id, db)

@router.get("/orders/print", response_model=ResponseModel)
def get_order_print(order_id: Optional[int] = None, db: Session = Depends(get_db)):
    """
    Retrieve order print data by ID
    """
    if not order_id:
        raise HTTPException(status_code=400, detail="Order ID is required")
    
    try:
        # Call your staff.get_order_print function
        result = staff.get_order_print(db, order_id)
        
        if not result:
            raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))