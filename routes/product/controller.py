from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
# from models import Account
from database import get_db
from response_model import ResponseModel
from routes.oauth2.repository import get_current_user
from routes.product.repository import Staff
from routes.product.model import *
# from routes.user.model import CreatePawn 

router = APIRouter(
    tags=["Product"],
    prefix="/api"
)

staff = Staff()
staff_service = Staff()

""" Update Product """
@router.post("/product", response_model = ResponseModel)
def create_product(product_info: CreateProduct, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    staff.is_staff(current_user)
    return staff.create_product(product_info, db, current_user)

""" Get All Product """
@router.get("/product", response_model=ResponseModel)
def get_all_product(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    staff.is_staff(current_user)
    return staff.get_product(db=db)

""" Update Existing Product """
@router.put("/product", response_model=ResponseModel)
def update_product(
    updated_product: UpdateProduct,  # Accept JSON as request body
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    staff_service = Staff()
    staff_service.is_staff(current_user)  # Ensure user is staff/admin

    return staff_service.update_product(
        db,
        prod_id=updated_product.prod_id,
        prod_name=updated_product.prod_name,
        unit_price=updated_product.unit_price,
        amount=updated_product.amount
    )

""" Delete Product """
@router.delete("/product/{product_id}")
def delete_product_by_id(
    product_id: int, 
    db: Session = Depends(get_db), 
    current_user: dict = Depends(get_current_user)
):
    staff.is_staff(current_user)
    return staff.delete_product_by_id(product_id, db)
