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
            
    def get_client_pawn(self, db: Session, cus_id: Optional[int] = None, cus_name: Optional[str] = None, phone_number: Optional[str] = None):
        client = db.query(Account).filter(
            and_(
                or_(
                    Account.cus_id == cus_id,
                    Account.phone_number == phone_number,
                    func.lower(Account.cus_name) == func.lower(cus_name)
                    ), 
                Account.role == 'user'
                )
            ).first()
        if not client:
            raise HTTPException(
                status_code=404,
                detail="Client not found",
            )
            
        get_detail_pawn = self.get_pawn_detail(db=db, cus_id=client.cus_id)
        if len(get_detail_pawn) <= 0:
            return ResponseModel(
                code=200,
                status="Success",
                message="Pawns not found",
                result=get_detail_pawn
            )
        
        return ResponseModel(
            code=200,
            status="Success",
            result=get_detail_pawn
        )
        
    def get_pawn_detail(
        self,
        db: Session,
        cus_id: Optional[int] = None,
        phone_number: Optional[str] = None,
        cus_name: Optional[str] = None,
    ):
        # Build filter conditions dynamically - only add conditions for non-None parameters
        search_conditions = []
        
        if cus_id is not None:
            search_conditions.append(Pawn.cus_id == cus_id)
        
        if phone_number is not None and phone_number.strip():
            search_conditions.append(Account.phone_number == phone_number.strip())
            
        if cus_name is not None and cus_name.strip():
            search_conditions.append(func.lower(Account.cus_name) == func.lower(cus_name.strip()))
        
        # If no search parameters provided, return empty result
        if not search_conditions:
            return []
        
        pawns = (
            db.query(
                Account.cus_id,  # 0
                Account.cus_name, # 1
                Account.phone_number, # 2
                Account.address, # 3
                Pawn.pawn_id, # 4
                Pawn.pawn_deposit, # 5
                Pawn.pawn_date, # 6
                Pawn.pawn_expire_date, # 7
                Product.prod_id, # 8
                Product.prod_name, # 9
                PawnDetail.pawn_weight, # 10
                PawnDetail.pawn_amount, # 11
                PawnDetail.pawn_unit_price, # 12
            )
            .select_from(Account)
            .join(Pawn, Account.cus_id == Pawn.cus_id)
            .join(PawnDetail, Pawn.pawn_id == PawnDetail.pawn_id)
            .join(Product, PawnDetail.prod_id == Product.prod_id)
            .filter(
                and_(
                    or_(*search_conditions),  # Only include non-None conditions
                    Account.role == "user",
                )
            )
            .all()
        )

        grouped_pawns = defaultdict(lambda: {
            "pawn_id": None,
            "cus_id": None,
            "customer_name": "",
            "phone_number": "",
            "address": "",
            "pawn_deposit": 0,
            "pawn_date": "",
            "pawn_expire_date": "",
            "products": [],
        })

        for pawn in pawns:
            pawn_id = pawn[4]
            if grouped_pawns[pawn_id]["pawn_id"] is None:
                grouped_pawns[pawn_id].update({
                    "pawn_id": pawn[4],
                    "cus_id": pawn[0],
                    "customer_name": pawn[1],
                    "phone_number": pawn[2],
                    "address": pawn[3],
                    "pawn_deposit": float(pawn[5]) if pawn[5] else 0,  # Handle potential None
                    "pawn_date": str(pawn[6]) if pawn[6] else "",  # Convert date to string
                    "pawn_expire_date": str(pawn[7]) if pawn[7] else "",  # Convert date to string
                })

            product = {
                "prod_id": pawn[8],
                "prod_name": pawn[9],
                "pawn_weight": pawn[10] or "",  # Handle potential None
                "pawn_amount": pawn[11] or 0,   # Handle potential None
                "pawn_unit_price": float(pawn[12]) if pawn[12] else 0,  # Handle potential None
            }

            # Check if product already exists before appending
            product_exists = any(
                p["prod_id"] == product["prod_id"] 
                for p in grouped_pawns[pawn_id]["products"]
            )
            if not product_exists:
                grouped_pawns[pawn_id]["products"].append(product)

        return list(grouped_pawns.values())