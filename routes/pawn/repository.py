from fastapi import HTTPException
from routes.user.model import *
from sqlalchemy.orm import Session
from entities import *
from response_model import ResponseModel
from typing import List, Dict
# from app.models import Client, Pawn
from sqlalchemy.sql import func, or_, and_
from sqlalchemy.exc import SQLAlchemyError
from collections import defaultdict
from typing import Dict, Any

class Staff:
    def is_staff(self, current_user: dict):
        if current_user['role'] != 'admin':
            raise HTTPException(
                status_code=403,
                detail="Permission denied",
            )
              
              
    def create_pawn(self, pawn_info: CreatePawn, db: Session, current_user: dict):
            if pawn_info.pawn_date > pawn_info.pawn_expire_date:
                raise HTTPException(
                    status_code=400,
                    detail="Pawn date must be before the expire date.",
                )

            # ✅ Check if the provided pawn_id already exists
            existing_pawn = db.query(Pawn).filter(Pawn.pawn_id == pawn_info.pawn_id).first()
            
            if existing_pawn:
                raise HTTPException(
                    status_code=400,
                    detail=f"Pawn record with ID {pawn_info.pawn_id} already exists."
                )

            # ✅ Check if customer exists by phone number or cus_id
            existing_customer = db.query(Account).filter(
                or_(
                    Account.phone_number == pawn_info.phone_number, 
                    Account.cus_id == pawn_info.cus_id
                ),
                Account.role == 'user'
            ).first()

            if existing_customer:
                # ✅ Update existing customer's name and address
                existing_customer.cus_name = pawn_info.cus_name
                existing_customer.address = pawn_info.address
                db.commit()
                db.refresh(existing_customer)
            else:
                # ✅ Create a new customer if not found
                existing_customer = self.create_client(
                    CreateClient(
                        cus_name=pawn_info.cus_name,
                        phone_number=pawn_info.phone_number,
                        address=pawn_info.address
                    ), 
                    db, 
                    True
                )

            # ✅ Create a new Pawn record
            pawn = Pawn(
                cus_id=existing_customer.cus_id,
                pawn_date=pawn_info.pawn_date,
                pawn_deposit=pawn_info.pawn_deposit,
                pawn_expire_date=pawn_info.pawn_expire_date
            )

            db.add(pawn)
            db.commit()
            db.refresh(pawn)

            # ✅ Insert Pawn Products (Allow multiple products per pawn)
            for product in pawn_info.pawn_product_detail:
                # 🔹 Ensure product exists or create new one
                existing_product = db.query(Product).filter(
                    Product.prod_name.ilike(product.prod_name)
                ).first()

                if not existing_product:
                    prod = self.create_product(CreateProduct(prod_name=product.prod_name), db, current_user)
                    prod_id = prod.prod_id
                else:
                    prod_id = existing_product.prod_id

                # ✅ Create PawnDetail for each product
                pawn_detail = PawnDetail(
                    pawn_id=pawn.pawn_id,
                    prod_id=prod_id,
                    pawn_weight=product.pawn_weight,
                    pawn_amount=product.pawn_amount,
                    pawn_unit_price=product.pawn_unit_price
                )

                db.add(pawn_detail)

            db.commit()  # ✅ Commit all pawn details at once for efficiency

            return ResponseModel(
                code=200,
                status="Success",
                message=f"Pawn record created successfully with multiple products. (Pawn ID: {pawn.pawn_id})"
            )

    def create_client(self, client_info: CreateClient, db: Session, not_exist: bool = False):
        existing_client = db.query(Account).filter(Account.phone_number == client_info.phone_number).first()
        if existing_client:
            raise HTTPException(
                status_code=400,
                detail="Phone Number already registered",
            )
        
        if not_exist:
            try:
                client = Account(
                    cus_name = client_info.cus_name, 
                    address = client_info.address,
                    phone_number = client_info.phone_number,)
                db.add(client)
                db.commit()
                db.refresh(client)
            except SQLAlchemyError as e:
                db.rollback()
                print(f"Error occurred: {str(e)}")
                raise HTTPException(status_code=500, detail="Database error occurred.")
            
            return client
            
        client = Account(
            cus_name = client_info.cus_name, 
            address = client_info.address,
            phone_number = client_info.phone_number,)
        
        db.add(client)
        db.commit()
        db.refresh(client)
        
        return ResponseModel(
            code=200,
            status="Success",
            message="Client created successfully"
        )
        
    def create_product(self, product_info: CreateProduct, db: Session, current_user: dict):
            existing_product = db.query(Product).filter(Product.prod_name == func.lower(product_info.prod_name)).first()
            if existing_product:
                raise HTTPException(
                    status_code=400,
                    detail="ផលិតផលមានរួចហើយ",
                )
                
            if product_info.amount != None and product_info.unit_price != None:
                product = Product(
                    prod_name = func.lower(product_info.prod_name),
                    unit_price = product_info.unit_price,
                    amount = product_info.amount,
                    user_id = current_user['id'])
                db.add(product)
                db.commit()
                db.refresh(product)
                
            else: 
                product = Product(prod_name = func.lower(product_info.prod_name), user_id = current_user['id'])
                db.add(product)
                db.commit()
                db.refresh(product)
                return product
            
            
            return ResponseModel(
                code=200,
                status="Success",
                message="ការបញ្ជាទិញត្រូវបានជោគជ័យ"
            )