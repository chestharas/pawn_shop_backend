from fastapi import HTTPException
from routes.user.model import *
from sqlalchemy.orm import Session
from entities import *
from response_model import ResponseModel
from typing import List, Dict, Optional
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
            message="ផលិតផលរក្សាទុកបានជោគជ័យ"
        )

    def get_client_order_id(self, db: Session, cus_id: int):
        """
        Get client details and their orders by customer ID
        """
        # First, check if the client exists
        client = db.query(Account).filter(
            and_(
                Account.cus_id == cus_id,
                Account.role == 'user'
            )
        ).first()
        
        if not client:
            raise HTTPException(
                status_code=404,
                detail="Client not found"
            )

        # Get client's order details
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
            .join(OrderDetail, Order.order_id == OrderDetail.order_id)
            .join(Product, OrderDetail.prod_id == Product.prod_id)
            .filter(Order.cus_id == cus_id)
            .all()
        )

        # Group orders by order_id
        grouped_orders = defaultdict(lambda: {
            "order_id": None,
            "order_deposit": 0,
            "order_date": "",
            "products": [],
        })

        for order in orders:
            order_id = order[0]

            if grouped_orders[order_id]["order_id"] is None:
                grouped_orders[order_id]["order_id"] = order_id
                grouped_orders[order_id]["order_deposit"] = order[1]
                grouped_orders[order_id]["order_date"] = order[2].strftime("%Y-%m-%d") if order[2] else ""

            product = {
                "prod_name": order[3],
                "prod_id": order[4],
                "order_weight": order[5],
                "order_amount": order[6],
                "product_sell_price": order[7],
                "product_labor_cost": order[8],
                "product_buy_price": order[9],
            }

            grouped_orders[order_id]["products"].append(product)

        # Prepare the result
        result = {
            "client_info": {
                "cus_id": client.cus_id,
                "cus_name": client.cus_name,
                "address": client.address,
                "phone_number": client.phone_number
            },
            "orders": list(grouped_orders.values()) if grouped_orders else []
        }

        return ResponseModel(
            code=200,
            status="Success",
            result=result
        )

    # ... (rest of your methods remain the same)
    
    def get_client_id(self, db: Session, cus_ids: List[int]):
        # Ensure we are filtering with multiple `cus_id`s
        orders = (
            db.query(
                # Order.order_id,
                Account.cus_id,
                Account.cus_name,
                
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

    def get_customers_with_orders(self, db: Session):
        clients = (
            db.query(Account.cus_id, Account.cus_name, Account.address)
            .join(Order, Order.cus_id == Account.cus_id)
            .filter(Account.role == 'user')
            .distinct()
            .all()
        )

        return ResponseModel(
            code=200,
            status="Success",
            result=clients
        )