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
            
    def get_client_pawn(self, db: Session, phone_number: Optional[str] = None, cus_name: Optional[str] = None, cus_id: Optional[int] = None):
        # Build dynamic filters based on provided parameters
        filters = [Account.role == 'user']

        if phone_number:
            filters.append(Account.phone_number == phone_number)
        if cus_name:
            filters.append(func.lower(Account.cus_name) == func.lower(cus_name))  # Case-insensitive search
        if cus_id:
            filters.append(Account.cus_id == cus_id)

        # Fetch ALL customers matching the search criteria with all required fields
        clients = db.query(
            Account.cus_id, 
            Account.cus_name, 
            Account.phone_number, 
            Account.address
        ).filter(and_(*filters)).all()

        if not clients:
            return ResponseModel(
                code=404,
                status="Error",
                message="Client not found",
                result=[]
            )

        # Convert to list of dictionaries for better JSON response
        clients_data = []
        for client in clients:
            clients_data.append({
                "cus_id": client.cus_id,
                "cus_name": client.cus_name,
                "phone_number": client.phone_number,
                "address": client.address
            })

        return ResponseModel(
            code=200,
            status="Success",
            message=f"Found {len(clients_data)} client(s)",
            result=clients_data
        )
        
    def get_pawn_detail(
        self,
        db: Session,
        cus_id: Optional[int] = None,
        phone_number: Optional[str] = None,
        cus_name: Optional[str] = None,
    ):
        """Get pawn details with search conditions - supports both single ID and list of IDs"""
        
        # Build filter conditions dynamically
        search_conditions = []
        
        if cus_id is not None:
            if isinstance(cus_id, list):
                if cus_id:  # Check if list is not empty
                    search_conditions.append(Pawn.cus_id.in_(cus_id))
            else:
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
                    or_(*search_conditions),
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
                    "pawn_deposit": float(pawn[5]) if pawn[5] else 0,
                    "pawn_date": str(pawn[6]) if pawn[6] else "",
                    "pawn_expire_date": str(pawn[7]) if pawn[7] else "",
                })

            product = {
                "prod_id": pawn[8],
                "prod_name": pawn[9],
                "pawn_weight": pawn[10] or "",
                "pawn_amount": pawn[11] or 0,
                "pawn_unit_price": float(pawn[12]) if pawn[12] else 0,
            }

            # Check if product already exists before appending
            product_exists = any(
                p["prod_id"] == product["prod_id"] 
                for p in grouped_pawns[pawn_id]["products"]
            )
            if not product_exists:
                grouped_pawns[pawn_id]["products"].append(product)

        return list(grouped_pawns.values())
        
    def get_all_pawn_details(self, db: Session):
        """Get all pawn details without search conditions"""
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
            .filter(Account.role == "user")
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
                    "pawn_deposit": float(pawn[5]) if pawn[5] else 0,
                    "pawn_date": str(pawn[6]) if pawn[6] else "",
                    "pawn_expire_date": str(pawn[7]) if pawn[7] else "",
                })

            product = {
                "prod_id": pawn[8],
                "prod_name": pawn[9],
                "pawn_weight": pawn[10] or "",
                "pawn_amount": pawn[11] or 0,
                "pawn_unit_price": float(pawn[12]) if pawn[12] else 0,
            }

            # Check if product already exists before appending
            product_exists = any(
                p["prod_id"] == product["prod_id"] 
                for p in grouped_pawns[pawn_id]["products"]
            )
            if not product_exists:
                grouped_pawns[pawn_id]["products"].append(product)

        return list(grouped_pawns.values())
    
    def get_all_client_pawn(self, db: Session):
        clients_with_pawns = db.query(
            Account.cus_id,
            Account.cus_name, 
            Account.address,
            Account.phone_number
        ).join(
            Pawn, Account.cus_id == Pawn.cus_id  # Changed from 'pawn' to 'Pawn'
        ).filter(
            Account.role == 'user'
        ).distinct().all()  # Use distinct to avoid duplicates

        if not clients_with_pawns:
            return ResponseModel(
                code=404,
                status="Not Found",
                message="No clients with pawns found",
                result=[]
            )

        # Convert to list of dictionaries
        clients_data = []
        for client in clients_with_pawns:
            clients_data.append({
                "cus_id": client.cus_id,
                "cus_name": client.cus_name,
                "address": client.address,
                "phone_number": client.phone_number
            })

        return ResponseModel(
            code=200,
            status="Success",
            result=clients_data
        )
        
    def get_client_id(self, cus_id: int, db: Session):
        # First check if client exists
        client = db.query(Account).filter(
            and_(
                Account.cus_id == cus_id,
                Account.role == 'user'
            )
        ).first()
        
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        # Get client's pawn details
        pawns = db.query(
            Pawn.pawn_id,           
            Pawn.pawn_deposit,      
            Pawn.pawn_date,         
            Product.prod_name,
            Product.prod_id,
            PawnDetail.pawn_weight,      
            PawnDetail.pawn_amount,      
            PawnDetail.pawn_unit_price,  
        ).join(PawnDetail, Pawn.pawn_id == PawnDetail.pawn_id)\
        .join(Product, PawnDetail.prod_id == Product.prod_id)\
        .filter(Pawn.cus_id == cus_id)\
        .all()
        
        # Group pawns by pawn_id
        grouped_pawns = defaultdict(lambda: {
            "pawn_id": None,
            "pawn_deposit": 0,
            "pawn_date": "",
            "products": [],
        })

        for pawn in pawns:
            pawn_id = pawn[0]

            if grouped_pawns[pawn_id]["pawn_id"] is None:
                grouped_pawns[pawn_id]["pawn_id"] = pawn_id
                grouped_pawns[pawn_id]["pawn_deposit"] = pawn[1]
                grouped_pawns[pawn_id]["pawn_date"] = pawn[2].strftime("%Y-%m-%d") if pawn[2] else ""

            product = {
                "prod_name": pawn[3],
                "prod_id": pawn[4],
                "pawn_weight": pawn[5],     
                "pawn_amount": pawn[6],     
                "pawn_unit_price": pawn[7], 
                
            }

            grouped_pawns[pawn_id]["products"].append(product)

        # Return the complete client and pawn information
        result = {
            "client_info": {
                "cus_id": client.cus_id,
                "cus_name": client.cus_name,
                "address": client.address,
                "phone_number": client.phone_number
            },
            "pawns": list(grouped_pawns.values()) if grouped_pawns else [],  # Changed from pawns
            "total_pawns": len(grouped_pawns) 
        }

        return ResponseModel(
            code=200,
            status="Success",
            result=result
        )
        
    def get_next_pawn_id(self, db: Session):
        try:
            # Get the highest pawn_id from the database
            # Adjust 'Pawn' and 'pawn_id' to match your actual model and field names
            max_pawn = db.query(func.max(Pawn.pawn_id)).scalar()
            
            # If no pawns exist, start with 1, otherwise increment by 1
            next_id = 1 if max_pawn is None else max_pawn + 1
            
            return ResponseModel(
                code=200,
                status="Success",
                result={"next_pawn_id": next_id}
            )
        except Exception as e:
            return ResponseModel(
                code=500,
                status="Error",
                message=f"Failed to get next pawn ID: {str(e)}"
            )
            
    def get_last_pawns(self, db: Session):
        """Get the last 3 most recently created pawns with all details"""
        try:
            # Get the last 3 pawns (highest pawn_ids)
            last_pawns = db.query(Pawn).order_by(Pawn.pawn_id.desc()).limit(3).all()
            
            if not last_pawns:
                return ResponseModel(
                    code=404,
                    status="Not Found",
                    message="No pawns found",
                    result=[]
                )
            
            pawns_result = []
            
            for pawn in last_pawns:
                # Get client information for each pawn
                client = db.query(Account).filter(
                    and_(
                        Account.cus_id == pawn.cus_id,
                        Account.role == 'user'
                    )
                ).first()
                
                # Get pawn details with products for each pawn
                pawn_details = db.query(
                    PawnDetail.pawn_weight,
                    PawnDetail.pawn_amount,
                    PawnDetail.pawn_unit_price,
                    Product.prod_name,
                    Product.prod_id
                ).join(Product, PawnDetail.prod_id == Product.prod_id)\
                .filter(PawnDetail.pawn_id == pawn.pawn_id)\
                .all()
                
                # Format products data for each pawn
                products = []
                total_amount = 0
                for detail in pawn_details:
                    product = {
                        "prod_name": detail.prod_name,
                        "prod_id": detail.prod_id,
                        "pawn_weight": detail.pawn_weight,
                        "pawn_amount": detail.pawn_amount,
                        "pawn_unit_price": detail.pawn_unit_price,
                        "subtotal": detail.pawn_amount * detail.pawn_unit_price
                    }
                    products.append(product)
                    total_amount += product["subtotal"]
                
                # Prepare each pawn's data
                pawn_data = {
                    "pawn_info": {
                        "pawn_id": pawn.pawn_id,
                        "pawn_date": pawn.pawn_date.strftime("%Y-%m-%d") if pawn.pawn_date else "",
                        "pawn_expire_date": pawn.pawn_expire_date.strftime("%Y-%m-%d") if pawn.pawn_expire_date else "",
                        "pawn_deposit": pawn.pawn_deposit,
                        "total_amount": total_amount,
                        "remaining_balance": total_amount - pawn.pawn_deposit
                    },
                    "client_info": {
                        "cus_id": client.cus_id,
                        "cus_name": client.cus_name,
                        "address": client.address,
                        "phone_number": client.phone_number
                    } if client else None,
                    "products": products,
                    "summary": {
                        "total_products": len(products),
                        "total_amount": total_amount,
                        "deposit_paid": pawn.pawn_deposit,
                        "balance_due": total_amount - pawn.pawn_deposit
                    }
                }
                
                pawns_result.append(pawn_data)
            
            return ResponseModel(
                code=200,
                status="Success",
                message=f"Last {len(pawns_result)} pawns retrieved successfully",
                result=pawns_result
            )
            
        except Exception as e:
            return ResponseModel(
                code=500,
                status="Error",
                message=f"Failed to retrieve last pawns: {str(e)}"
            )

    def get_pawn_print(self, db: Session, pawn_id: Optional[int] = None):
        """
        Retrieve all pawn records or a specific pawn by ID along with customer and product details.
        """
        # Query to fetch all pawn records (or filter by pawn_id if provided)
        pawn_query = (
            db.query(
                Account.cus_id,
                Account.cus_name,
                Account.phone_number,
                Account.address,
                Pawn.pawn_id,
                Pawn.pawn_deposit,
                Pawn.pawn_date,
                Pawn.pawn_expire_date,
                Product.prod_id,
                Product.prod_name,
                PawnDetail.pawn_weight,
                PawnDetail.pawn_amount,
                PawnDetail.pawn_unit_price,
            )
            .join(Pawn, Account.cus_id == Pawn.cus_id)
            .join(PawnDetail, Pawn.pawn_id == PawnDetail.pawn_id)
            .join(Product, PawnDetail.prod_id == Product.prod_id)
            .filter(Account.role == "user")
        )

        # If pawn_id is provided, filter the query
        if pawn_id:
            pawn_query = pawn_query.filter(Pawn.pawn_id == pawn_id)

        pawns = pawn_query.all()

        # If no pawn records found, return a 404 response
        if not pawns:
            return ResponseModel(
                code=404,
                status="Error",
                message=f"No pawn record found for pawn ID {pawn_id}." if pawn_id else "No pawn records found.",
                result=[]
            )

        # Structure the response differently based on whether we're fetching a single pawn or all pawns
        if pawn_id:
            # Single pawn response - more detailed structure
            pawn_data = pawns[0]  # Get first row for basic info
            
            # Calculate totals for the pawn
            total_amount = sum(float(pawn[11]) if pawn[11] else 0 for pawn in pawns)  # pawn_amount
            total_weight = sum(float(pawn[10]) if pawn[10] else 0 for pawn in pawns)  # pawn_weight
            
            response_data = {
                "pawn_id": pawn_data[4],
                "pawn_deposit": pawn_data[5],
                "pawn_date": pawn_data[6].strftime("%Y-%m-%d %H:%M:%S"),
                "pawn_expire_date": pawn_data[7].strftime("%Y-%m-%d %H:%M:%S") if pawn_data[7] else None,
                "total_amount": total_amount,
                "total_weight": total_weight,
                "customer": {
                    "cus_id": pawn_data[0],
                    "customer_name": pawn_data[1],
                    "phone_number": pawn_data[2],
                    "address": pawn_data[3]
                },
                "products": []
            }
            
            # Add all products for this pawn
            for pawn in pawns:
                response_data["products"].append({
                    "prod_id": pawn[8],
                    "prod_name": pawn[9],
                    "pawn_weight": pawn[10],
                    "pawn_amount": pawn[11],
                    "pawn_unit_price": pawn[12],
                })
            
            return ResponseModel(
                code=200,
                status="Success",
                message=f"Pawn {pawn_id} retrieved successfully.",
                result=response_data
            )
        
        else:
            # Multiple pawns response - grouped by customer
            pawn_list = {}
            
            for pawn in pawns:
                cus_id = pawn[0]
                pawn_id_current = pawn[4]

                if cus_id not in pawn_list:
                    pawn_list[cus_id] = {
                        "cus_id": cus_id,
                        "customer_name": pawn[1],
                        "phone_number": pawn[2],
                        "address": pawn[3],
                        "pawns": {}
                    }

                # Group products by pawn_id within each customer
                if pawn_id_current not in pawn_list[cus_id]["pawns"]:
                    pawn_list[cus_id]["pawns"][pawn_id_current] = {
                        "pawn_id": pawn_id_current,
                        "pawn_deposit": pawn[5],
                        "pawn_date": pawn[6].strftime("%Y-%m-%d %H:%M:%S"),
                        "pawn_expire_date": pawn[7].strftime("%Y-%m-%d %H:%M:%S") if pawn[7] else None,
                        "products": [],
                        "pawn_total_amount": 0,
                        "pawn_total_weight": 0
                    }

                # Add product to the specific pawn
                product_data = {
                    "prod_id": pawn[8],
                    "prod_name": pawn[9],
                    "pawn_weight": pawn[10],
                    "pawn_amount": pawn[11],
                    "pawn_unit_price": pawn[12],
                }
                
                pawn_list[cus_id]["pawns"][pawn_id_current]["products"].append(product_data)
                pawn_list[cus_id]["pawns"][pawn_id_current]["pawn_total_amount"] += float(pawn[11]) if pawn[11] else 0
                pawn_list[cus_id]["pawns"][pawn_id_current]["pawn_total_weight"] += float(pawn[10]) if pawn[10] else 0

            # Convert nested dict structure to list format
            result = []
            for customer_data in pawn_list.values():
                customer_data["pawns"] = list(customer_data["pawns"].values())
                result.append(customer_data)

            # Return a successful response
            return ResponseModel(
                code=200,
                status="Success",
                message=f"Retrieved {len(result)} customers with pawn records.",
                result=result
            )