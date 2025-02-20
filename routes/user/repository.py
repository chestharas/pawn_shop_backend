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
                detail="Product already exists",
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
        
    def create_order(self, order_info: CreateOrder, db: Session, current_user: dict):
        existing_customer = db.query(Account).filter(
            and_(
                or_(
                    Account.phone_number == order_info.phone_number, 
                    Account.cus_id == order_info.cus_id
                ), 
                Account.role == 'user'
            )
        ).first()

        if existing_customer:
            # ✅ Update existing customer's name and address
            existing_customer.cus_name = order_info.cus_name
            existing_customer.address = order_info.address
            db.commit()
            db.refresh(existing_customer)
        else:
            # ✅ Create new customer if not found
            existing_customer = self.create_client(
                CreateClient(
                    cus_name=order_info.cus_name, 
                    phone_number=order_info.phone_number, 
                    address=order_info.address
                ), 
                db, 
                True
            )

        # ✅ Check if order_id is provided, if it exists, return an error
        if hasattr(order_info, "order_id") and order_info.order_id:
            existing_order = db.query(Order).filter(Order.order_id == order_info.order_id).first()
            if existing_order:
                return ResponseModel(
                    code=400,
                    status="Error",
                    message="ផលិតផលបានរក្សាទុករួចរាល់ហើយ"
                )

        # ✅ Create a new order if order_id is not provided
        order = Order(
            cus_id=existing_customer.cus_id,
            order_deposit=order_info.order_deposit
        )
        db.add(order)
        db.commit()
        db.refresh(order)

        for product in order_info.order_product_detail:
            existing_product = db.query(Product).filter(
                Product.prod_name == func.lower(product.prod_name)
            ).first()

            if not existing_product:
                prod = self.create_product(CreateProduct(prod_name=product.prod_name), db, current_user)
                prod_id = prod.prod_id
            else:
                prod_id = existing_product.prod_id

            # ✅ Add order details (always create new details, do not delete old ones)
            order_detail = OrderDetail(
                order_id=order.order_id,
                prod_id=prod_id,
                order_weight=product.order_weight,
                order_amount=product.order_amount,
                product_sell_price=product.product_sell_price,
                product_labor_cost=product.product_labor_cost,
                product_buy_price=product.product_buy_price,
            )

            db.add(order_detail)

        db.commit()  # Commit all order details at once

        return ResponseModel(
            code=200,
            status="Success",
            message="Order created successfully"
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



            
    def get_product(self, db: Session):
        products = db.query(Product).all()
        if not products:
            raise HTTPException(
                status_code=404,
                detail="Products not found",
            )
        serialized_products = [
            {
                "id": product.prod_id,
                "name": product.prod_name,
                "price": product.unit_price,
                "amount": product.amount,
            }
            for product in products
        ]
        return ResponseModel(
            code=200,
            status="Success",
            result=serialized_products
        )
    
    # def get_product(self, db: Session):
    #     products = db.query(Product).all()
    #     if not products:
    #         raise HTTPException(
    #             status_code=404,
    #             detail="Products not found",
    #         )
    #     serialized_products = []
    #     for product in products:
    #         # Default values
    #         unit_price = product.unit_price
    #         amount = product.amount  # Default to product.amount
    #         order_amount = None  # Default in case no OrderDetail exists
            
    #         # Check and fallback for unit_price and amount
    #         if unit_price is None or amount is None:
    #             order_detail = db.query(OrderDetail).filter(
    #                 OrderDetail.prod_id == product.prod_id
    #             ).first()
    #             if order_detail:
    #                 unit_price = unit_price or order_detail.product_buy_price
    #                 amount = amount or order_detail.order_amount  # Fallback for amount
    
    #         serialized_products.append(
    #             {
    #                 "id": product.prod_id,
    #                 "name": product.prod_name,
    #                 "price": unit_price,
    #                 "amount": amount,  # Use the fallback value
    #             }
    #         )
    #     return ResponseModel(
    #         code=200,
    #         status="Success",
    #         result=serialized_products
    #     )

    def get_order_account(
        self,
        db: Session,
        phone_number: Optional[str] = None,
    ):
        orders = (
            db.query(
                Account.cus_name,
                Account.cus_id,
                Account.address
            )
            .filter(
                and_(
                    Account.phone_number == phone_number,
                    Account.role == "user",
                )
            )
            .all()
        )

        result = [
            {
                "cus_name": order.cus_name,
                "customer_id": order.cus_id,
                "address": order.address
            }
            for order in orders
        ]

        return result


    def get_product(self, db: Session):
        products = db.query(Product).all()
        if not products:
            raise HTTPException(
                status_code=404,
                detail="Products not found",
            )
        serialized_products = [
            {
                "id": product.prod_id,
                "name": product.prod_name,
                "price": product.unit_price,
                "amount": product.amount,
            }
            for product in products
        ]
        return ResponseModel(
            code=200,
            status="Success",
            result=serialized_products
        )
        
        


    def get_client(self, db: Session):
        clients = db.query(Account).filter(Account.role == 'user').all()
        return ResponseModel(
            code=200,
            status="Success",
            result=clients
        )
        
    def get_order_by_id(self, db: Session, order_id: Optional[int] = None):
        """
        Retrieve all orders or a specific order by ID along with customer details.
        """
        # Fetch all orders (or a specific order if order_id is provided)
        order_query = (
            db.query(
                Account.cus_id,
                Account.cus_name,
                Account.phone_number,
                Account.address,
                Order.order_id,
                Order.order_deposit,
                Order.order_date,
                Product.prod_id,
                Product.prod_name,
                OrderDetail.order_weight,
                OrderDetail.order_amount,
                OrderDetail.product_sell_price,
                OrderDetail.product_labor_cost,
                OrderDetail.product_buy_price,
            )
            .join(Order, Account.cus_id == Order.cus_id)
            .join(OrderDetail, Order.order_id == OrderDetail.order_id)
            .join(Product, OrderDetail.prod_id == Product.prod_id)
            .filter(Account.role == "user")
        )

        # If order_id is provided, filter the query
        if order_id:
            order_query = order_query.filter(Order.order_id == order_id)

        orders = order_query.all()

        # If no orders found, return an empty response
        if not orders:
            return ResponseModel(
                code=404,
                status="Error",
                message="No orders found for the given order ID." if order_id else "No orders found.",
                result=[]
            )

        # Structure response
        order_list = {}
        for order in orders:
            cus_id = order[0]

            if cus_id not in order_list:
                order_list[cus_id] = {
                    "cus_id": cus_id,
                    "customer_name": order[1],
                    "phone_number": order[2],
                    "address": order[3],
                    "orders": []
                }

            order_list[cus_id]["orders"].append({
                "order_id": order[4],
                "order_deposit": order[5],
                "order_date": str(order[6]),  # Convert date to string format
                "product": {
                    "prod_id": order[7],
                    "prod_name": order[8],
                    "order_weight": order[9],
                    "order_amount": order[10],
                    "product_sell_price": order[11],
                    "product_labor_cost": order[12],
                    "product_buy_price": order[13],
                }
            })

        return ResponseModel(
            code=200,
            status="Success",
            result=list(order_list.values())  # Convert dict to list
        )

        
    def get_order_detail(self, db: Session, cus_ids: List[int]):
        # Ensure we are filtering with multiple `cus_id`s
        orders = (
            db.query(
                Order.order_id,
                Order.order_deposit,
                Order.order_date,
                Product.prod_name,
                Product.prod_id,
                OrderDetail.order_weight,
                OrderDetail.order_amount,
                OrderDetail.product_sell_price,
                OrderDetail.product_labor_cost,
                OrderDetail.product_buy_price,
            )
            .join(Order, OrderDetail.order_id == Order.order_id)
            .join(Product, OrderDetail.prod_id == Product.prod_id)
            .filter(Order.cus_id.in_(cus_ids))  # Fetch orders for multiple `cus_id`s
            .all()
        )

        grouped_orders = defaultdict(lambda: {
            "order_id": None,
            "order_deposit": 0,
            "order_date": "",
            "products": [],
        })

        for order in orders:
            order_id = order[0]  # `order_id`

            if grouped_orders[order_id]["order_id"] is None:
                grouped_orders[order_id]["order_id"] = order_id
                grouped_orders[order_id]["order_deposit"] = order[1]
                grouped_orders[order_id]["order_date"] = order[2]  # Order Date

            product = {
                "prod_name": order[3],  # Product Name
                "prod_id": order[4],  # Product ID
                "order_weight": order[5],  # Product Weight
                "order_amount": order[6],  # Order Amount
                "product_sell_price": order[7],  # Sell Price
                "product_labor_cost": order[8],  # Labor Cost
                "product_buy_price": order[9],  # Buy Price
            }

            grouped_orders[order_id]["products"].append(product)  # Append products correctly

        return list(grouped_orders.values())  # Return all orders


# ======================================= Order search ===========================================================

    def get_client_order(self, db: Session, phone_number: Optional[str] = None, cus_name: Optional[str] = None, cus_id: Optional[int] = None):
        # Build dynamic filters based on provided parameters
        filters = [Account.role == 'user']

        if phone_number:
            filters.append(Account.phone_number == phone_number)
        if cus_name:
            filters.append(func.lower(Account.cus_name) == func.lower(cus_name))  # Case-insensitive search
        if cus_id:
            filters.append(Account.cus_id == cus_id)

        # Fetch ALL customers matching the search criteria
        clients = db.query(Account.cus_id, Account.cus_name).filter(and_(*filters)).all()

        if not clients:
            raise HTTPException(
                status_code=404,
                detail="Client not found",
            )

        # Extract customer IDs and names from query result
        cus_ids = [client.cus_id for client in clients]

        # Fetch all orders related to those customer IDs
        get_detail_order = self.get_order_detail(db=db, cus_ids=cus_ids)  # Pass list of `cus_id`s

        if not get_detail_order:
            return ResponseModel(
                code=200,
                status="Success",
                message="Orders not found",
                result=[]
            )

        return ResponseModel(
            code=200,
            status="Success",
            result=get_detail_order
        )




    def get_order_account(
        self,
        db: Session,
        phone_number: Optional[str] = None,
    ):
        orders = (
            db.query(
                Account.cus_name,
                Account.cus_id,
                Account.address
            )
            .filter(
                and_(
                    Account.phone_number == phone_number,
                    Account.role == "user",
                )
            )
            .all()
        )

        result = [
            {
                "cus_name": order.cus_name,
                "cus_id": order.cus_id,
                "address": order.address
            }
            for order in orders
        ]

        return result

        
    def get_client_by_phone (self, db: Session, phone_number: str):
        client = db.query(Account).filter(
            and_(
                Account.phone_number == phone_number,
                Account.role == 'user'
            )
        ).first()

        if not client:
            raise HTTPException(
                status_code=404,
                detail="Client not found",
            )

        get_account_order = self.get_order_account(db=db, phone_number=phone_number)

        if not get_account_order:
            return ResponseModel(
                code=200,
                status="Success",
                message="Orders not found",
                result=get_account_order
            )

        return ResponseModel(
            code=200,
            status="Success",
            result=get_account_order
        )

        # ======================================= Order search =========================================================== 
        
    def get_pawn_detail(
            self,
            db: Session,
            cus_id: Optional[int] = None,
            phone_number: Optional[str] = None,
            cus_name: Optional[str] = None,
        ):
            pawns = (
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
                .select_from(Account)
                .join(Pawn, Account.cus_id == Pawn.cus_id)
                .join(PawnDetail, Pawn.pawn_id == PawnDetail.pawn_id)
                .join(Product, PawnDetail.prod_id == Product.prod_id)
                .filter(
                    and_(
                        or_(
                            Pawn.cus_id == cus_id,
                            Account.phone_number == phone_number,
                            func.lower(Account.cus_name) == func.lower(str(cus_name)),
                        ),
                        Account.role == "user",
                    )
                )
                .all()
            )
    
            grouped_pawns = defaultdict(lambda: {
                "pawn_id": None,  #  Add pawn_id at the top level
                "cus_id": None,  #  Include cus_id
                "customer_name": "",
                "phone_number": "",
                "address": "",
                "pawn_deposit": 0,
                "pawn_date": "",
                "pawn_expire_date": "",
                "products": [],
            })
    
            for pawn in pawns:
                pawn_id = pawn[4]  #  Ensure pawn_id is retrieved
                if grouped_pawns[pawn_id]["pawn_id"] is None:
                    grouped_pawns[pawn_id].update(
                        {
                            "pawn_id": pawn[4],  #  Include pawn_id
                            "cus_id": pawn[0],  #  Include customer ID
                            "customer_name": pawn[1],  #  Include customer name
                            "phone_number": pawn[2],
                            "address": pawn[3],
                            "pawn_deposit": pawn[5],
                            "pawn_date": pawn[6],
                            "pawn_expire_date": pawn[7],
                        }
                    )
    
                product = {
                    # "pawn_id": pawn[4],
                    "prod_id": pawn[8],
                    "prod_name": pawn[9],
                    "pawn_weight": pawn[10],
                    "pawn_amount": pawn[11],
                    "pawn_unit_price": pawn[12],
                }
    
                #  Check if product already exists before appending
                product_exists = any(p["prod_id"] == product["prod_id"] for p in grouped_pawns[pawn_id]["products"])
                if not product_exists:
                    grouped_pawns[pawn_id]["products"].append(product)
    
            #  Ensure pawn_id is included in every returned pawn record
            return list(grouped_pawns.values())
    
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
        
    def delete_product_by_id(self, product_id: int, db: Session):
        """
        Deletes a product by its ID.
        """
        product = db.query(Product).filter(Product.prod_id == product_id).first()
        if not product:
            # Instead of raising an exception, return a success message
            return ResponseModel(
                code=200,
                status="Success",
                message=f"Product with ID {product_id} not found but considered deleted"
            )

        try:
            db.delete(product)
            db.commit()
            return ResponseModel(
                code=200,
                status="Success",
                message=f"Product with ID {product_id} deleted successfully"
            )
        except SQLAlchemyError as e:
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Database error occurred: {str(e)}",
            )


    def delete_product_by_name(self, product_name: str, db: Session):
        """
        Deletes a product by its name.
        """
        product = db.query(Product).filter(func.lower(Product.prod_name) == func.lower(product_name)).first()
        if not product:
            raise HTTPException(
                status_code=404,
                detail=f"Product with name '{product_name}' not found",
            )
        
        try:
            db.delete(product)
            db.commit()
            return ResponseModel(
                code=200,
                status="Success",
                message=f"Product with name '{product_name}' deleted successfully"
            )
        except SQLAlchemyError as e:
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Database error occurred: {str(e)}",
            )

    def delete_all_products(self, db: Session):
        """
        Deletes all products from the database.
        """
        try:
            num_deleted = db.query(Product).delete()
            db.commit()
            return ResponseModel(
                code=200,
                status="Success",
                message=f"All products deleted successfully. Total deleted: {num_deleted}",
            )
        except SQLAlchemyError as e:
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Database error occurred: {str(e)}",
            )
            
    def get_product_by_id(self, product_id: int, db: Session) -> Dict:
        """
        Fetch a product by its ID and return it in a serialized format.
        """
        product = db.query(Product).filter(Product.prod_id == product_id).first()
        if not product:
            raise HTTPException(
                status_code=404,
                detail=f"Product with ID {product_id} not found"
            )
        # Serialize the product
        return {
            "id": product.prod_id,  # Changed key name to match the format in `get_product`
            "name": product.prod_name,
            "price": product.unit_price,
            "amount": product.amount,
        }
        
    def get_product_by_name(self, product_name: str, db: Session) -> List[Dict]:
        """
        Fetch products by their name and return them in a serialized format.
        """
        products = db.query(Product).filter(Product.prod_name.ilike(f"%{product_name}%")).all()
        if not products:
            raise HTTPException(
                status_code=404,
                detail=f"No products found with name '{product_name}'"
            )
        # Serialize the products
        return [
            {
                "id": product.prod_id,  # Changed key name to match the format in `get_product`
                "name": product.prod_name,
                "price": product.unit_price,
                "amount": product.amount,
            }
            for product in products
        ]
        
        
        
# ================================Get next ID family===============================================================================
# =================================================================================================================================


    def get_next_product_id(self, db: Session):
        """
        Retrieve the last product ID and return the next available ID.
        """
        try:
            last_product = db.query(Product.prod_id).order_by(Product.prod_id.desc()).first()

            next_product_id = last_product.prod_id + 1 if last_product else 1  # Start from 1 if no product exists

            return {
                "code": 200,
                "status": "Success",
                "result": {"id": next_product_id}
            }
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    def get_next_client_id(self, db: Session):
        """
        Retrieve the last client ID and return the next available ID.
        """
        try:
            last_client = db.query(Account.cus_id).filter(Account.role == "user").order_by(Account.cus_id.desc()).first()

            next_client_id = last_client.cus_id + 1 if last_client else 1  # Start from 1 if no client exists

            return {
                "code": 200,
                "status": "Success",
                "result": {"id": next_client_id}
            }
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        
    def get_next_order_id(self, db: Session):
        """
        Retrieve the last order ID and return the next available ID.
        """
        try:
            last_order = db.query(Order.order_id).order_by(Order.order_id.desc()).first()

            next_order_id = last_order.order_id + 1 if last_order else 1  # Start from 1 if no order exists

            return {
                "code": 200,
                "status": "Success",
                "result": {"id": next_order_id}
            }
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    def get_next_pawn_id(self, db: Session):
        """
        Retrieve the last pawn ID and return the next available ID.
        """
        try:
            last_pawn = db.query(Pawn.pawn_id).order_by(Pawn.pawn_id.desc()).first()

            next_pawn_id = last_pawn.pawn_id + 1 if last_pawn else 1  # Start from 1 if no pawn exists

            return {
                "code": 200,
                "status": "Success",
                "result": {"id": next_pawn_id}
            }
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# =================================================================================================================================

    def update_product(
        self,
        db: Session,
        prod_id: Optional[int] = None,
        prod_name: Optional[str] = None,
        unit_price: Optional[float] = None,
        amount: Optional[int] = None,
    ):
        if not prod_id and not prod_name:
            raise HTTPException(
                status_code=400,
                detail="Product ID or Name is required to update the product.",
            )

        # Search for product by ID or Name
        product_query = db.query(Product)
        if prod_id:
            product_query = product_query.filter(Product.prod_id == prod_id)
        elif prod_name:
            product_query = product_query.filter(Product.prod_name.ilike(prod_name))

        product = product_query.first()

        if not product:
            raise HTTPException(
                status_code=404,
                detail="Product not found.",
            )

        # Update only amount and price if provided
        if unit_price is not None:
            product.unit_price = unit_price
        if amount is not None:
            product.amount = amount

        db.commit()
        db.refresh(product)

        return ResponseModel(
            code=200,
            status="Success",
            message="Product updated successfully",
            result={
                "id": product.prod_id,
                "name": product.prod_name,
                "price": product.unit_price,
                "amount": product.amount,
            }
        )


    

    def get_all_pawns(self, db: Session, cus_id: int = None, cus_name: str = None, phone_number: str = None):
        """
        Retrieve all pawn transactions with customer and product details.
        If search parameters (cus_id, cus_name, phone_number) are provided, filter the records.
        Otherwise, return all records.
        """
        query = (
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
        )

        # Apply filters if search parameters are provided
        if cus_id or cus_name or phone_number:
            query = query.filter(
                and_(
                    or_(
                        (cus_id is not None and Account.cus_id == cus_id),
                        (cus_name is not None and func.lower(Account.cus_name).contains(func.lower(cus_name))),
                        (phone_number is not None and Account.phone_number.contains(phone_number)),
                    ),
                    Account.role == "user"
                )
            )

        query = query.order_by(Pawn.pawn_id.desc())  # Sort by latest pawn records
        pawns = query.all()

        if not pawns:
            return ResponseModel(
                code=200,
                status="Success",
                message="No pawn records found",
                result=[]
            )

        # Group the results by cus_id
        grouped_pawns = defaultdict(lambda: {
            "cus_id": 0,
            "customer_name": "",
            "phone_number": "",
            "address": "",
            "pawn_deposit": 0,
            "pawn_date": "",
            "pawn_expire_date": "",
            "products": [],
        })

        for pawn in pawns:
            cus_id = pawn[0]  # Extract cus_id

            # Populate customer details only once
            if not grouped_pawns[cus_id]["customer_name"]:
                grouped_pawns[cus_id].update({
                    "pawn_id": pawn[4],
                    "cus_id": pawn[0],
                    "customer_name": pawn[1],
                    "phone_number": pawn[2],
                    "address": pawn[3],
                    "pawn_deposit": pawn[5],
                    "pawn_date": pawn[6],
                    "pawn_expire_date": pawn[7],
                })

            # Add product details
            product = {
                "prod_id": pawn[8],
                "prod_name": pawn[9],
                "pawn_weight": pawn[10],
                "pawn_amount": pawn[11],
                "pawn_unit_price": pawn[12],
            }

            grouped_pawns[cus_id]["products"].append(product)

        return ResponseModel(
            code=200,
            status="Success",
            result=list(grouped_pawns.values())
        )
        
    