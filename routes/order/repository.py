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
        # Check for existing client by phone_number
        existing_client = db.query(Account).filter(
            Account.phone_number == client_info.phone_number,
            Account.role == 'user'
        ).first()

        if existing_client:
            raise HTTPException(
                status_code=400,
                detail="Phone Number already registered",
            )
        
        if not_exist:
            try:
                client = Account(
                    cus_name=client_info.cus_name,
                    address=client_info.address,
                    phone_number=client_info.phone_number,
                    role='user'  # Ensure role is set
                )
                db.add(client)
                db.commit()
                db.refresh(client)
            except SQLAlchemyError as e:
                db.rollback()
                print(f"Error occurred: {str(e)}")
                raise HTTPException(status_code=500, detail="Database error occurred.")
            
            return client
            
        client = Account(
            cus_name=client_info.cus_name,
            address=client_info.address,
            phone_number=client_info.phone_number,
            role='user'  # Ensure role is set
        )
        
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
                or_(Account.cus_id == order_info.cus_id),  # Simplified (removed duplicate)
                Account.role == 'user'
            )
        ).first()

        if existing_customer:
            existing_customer.cus_name = order_info.cus_name
            existing_customer.address = order_info.address
            db.commit()
            db.refresh(existing_customer)
        else:
            existing_customer = self.create_client(
                CreateClient(
                    cus_name=order_info.cus_name,
                    address=order_info.address,
                    phone_number=order_info.phone_number  # Only these fields
                ),
                db,
                True
            )

        # Rest of the method remains the same...
        if hasattr(order_info, "order_id") and order_info.order_id:
            existing_order = db.query(Order).filter(Order.order_id == order_info.order_id).first()
            if existing_order:
                return ResponseModel(
                    code=400,
                    status="Error",
                    message="ផលិតផលបានរក្សាទុករួចរាល់ហើយ"
                )

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

        db.commit()

        return ResponseModel(
            code=200,
            status="Success",
            message="ផលិតផលរក្សាទុកបានជោគជ័យ"
        )
        
    def get_client_order(self, db: Session, phone_number: Optional[str] = None, cus_name: Optional[str] = None, cus_id: Optional[int] = None):
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
        
    def get_order_account(
        self,
        db: Session,
        cus_id: Optional[str] = None,
    ):
        orders = (
            db.query(
                Account.cus_name,
                Account.cus_id,
                Account.address
            )
            .filter(
                and_(
                    Account.cus_id == cus_id,
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

    def get_all_client_order(self, db: Session):
        clients_with_orders = db.query(
            Account.cus_id,
            Account.cus_name, 
            Account.address,
            Account.phone_number
        ).join(
            Order, Account.cus_id == Order.cus_id  # Assuming you have an Order table
        ).filter(
            Account.role == 'user'
        ).distinct().all()  # Use distinct to avoid duplicates

        if not clients_with_orders:
            return ResponseModel(
                code=404,
                status="Not Found",
                message="No clients with orders found",
                result=[]
            )

        # Convert to list of dictionaries
        clients_data = []
        for client in clients_with_orders:
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
    
    def get_client_id(self, cus_id: int, db: Session):  # Changed from str to int
        # First check if client exists
        client = db.query(Account).filter(
            and_(
                Account.cus_id == cus_id,
                Account.role == 'user'
            )
        ).first()
        
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        # Get client's order details
        orders = db.query(
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
        ).join(OrderDetail, Order.order_id == OrderDetail.order_id)\
        .join(Product, OrderDetail.prod_id == Product.prod_id)\
        .filter(Order.cus_id == cus_id)\
        .all()
        
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

        # Return the complete client and order information
        result = {
            "client_info": {
                "cus_id": client.cus_id,
                "cus_name": client.cus_name,
                "address": client.address,
                "phone_number": client.phone_number
            },
            "orders": list(grouped_orders.values()) if grouped_orders else [],
            "total_orders": len(grouped_orders)
        }

        return ResponseModel(
            code=200,
            status="Success",
            result=result
        )
    def get_next_order_id(self, db: Session):
        try:
            # Get the highest order_id from the database
            max_order = db.query(func.max(Order.order_id)).scalar()
            
            # If no orders exist, start with 1, otherwise increment by 1
            next_id = 1 if max_order is None else max_order + 1
            
            return ResponseModel(
                code=200,
                status="Success",
                result={"next_order_id": next_id}
            )
        except Exception as e:
            return ResponseModel(
                code=500,
                status="Error",
                message=f"Failed to get next order ID: {str(e)}"
            )
            
    def get_last_order(self, db: Session):
        """Get the last 3 most recently created orders with all details"""
        try:
            # Get the last 3 orders (highest order_ids)
            last_orders = db.query(Order).order_by(Order.order_id.desc()).limit(3).all()
            
            if not last_orders:
                return ResponseModel(
                    code=404,
                    status="Not Found",
                    message="No orders found",
                    result=[]
                )
            
            orders_result = []
            
            for order in last_orders:
                # Get client information for each order
                client = db.query(Account).filter(
                    and_(
                        Account.cus_id == order.cus_id,
                        Account.role == 'user'
                    )
                ).first()
                
                # Get order details with products for each order
                order_details = db.query(
                    OrderDetail.order_weight,
                    OrderDetail.order_amount,
                    OrderDetail.product_sell_price,
                    OrderDetail.product_labor_cost,
                    OrderDetail.product_buy_price,
                    Product.prod_name,
                    Product.prod_id
                ).join(Product, OrderDetail.prod_id == Product.prod_id)\
                .filter(OrderDetail.order_id == order.order_id)\
                .all()
                
                # Format products data for each order
                products = []
                total_amount = 0
                for detail in order_details:
                    product = {
                        "prod_name": detail.prod_name,
                        "prod_id": detail.prod_id,
                        "order_weight": detail.order_weight,
                        "order_amount": detail.order_amount,
                        "product_sell_price": detail.product_sell_price,
                        "product_labor_cost": detail.product_labor_cost,
                        "product_buy_price": detail.product_buy_price,
                        "subtotal": detail.order_amount * detail.product_sell_price
                    }
                    products.append(product)
                    total_amount += product["subtotal"]
                
                # Prepare each order's data
                order_data = {
                    "order_info": {
                        "order_id": order.order_id,
                        "order_date": order.order_date.strftime("%Y-%m-%d %H:%M:%S") if order.order_date else "",
                        "order_deposit": order.order_deposit,
                        "total_amount": total_amount,
                        "remaining_balance": total_amount - order.order_deposit
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
                        "deposit_paid": order.order_deposit,
                        "balance_due": total_amount - order.order_deposit
                    }
                }
                
                orders_result.append(order_data)
            
            return ResponseModel(
                code=200,
                status="Success",
                message=f"Last {len(orders_result)} orders retrieved successfully",
                result=orders_result
            )
            
        except Exception as e:
            return ResponseModel(
                code=500,
                status="Error",
                message=f"Failed to retrieve last orders: {str(e)}"
            )

    def get_order_print(self, db: Session, order_id: Optional[int] = None):
        """
        Retrieve all orders or a specific order by ID along with customer details.
        """
        # Base query for fetching order data
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

        # Filter by specific order_id if provided
        if order_id:
            order_query = order_query.filter(Order.order_id == order_id)

        orders = order_query.all()

        # Handle empty results
        if not orders:
            return ResponseModel(
                code=404,
                status="Error",
                message=f"No order found with ID {order_id}." if order_id else "No orders found.",
                result=[]
            )

        # Structure the response differently based on whether we're fetching a single order or all orders
        if order_id:
            # Single order response - more detailed structure
            order_data = orders[0]  # Get first row for basic info
            
            # Calculate totals for the order
            total_amount = sum(order[10] for order in orders)  # order_amount
            total_cost = sum((order[12] or 0) + (order[13] or 0) for order in orders)  # labor_cost + buy_price
            
            response_data = {
                "order_id": order_data[4],
                "order_deposit": order_data[5],
                "order_date": order_data[6].strftime("%Y-%m-%d %H:%M:%S"),
                "total_amount": total_amount,
                "total_cost": total_cost,
                "profit": total_amount - total_cost,
                "customer": {
                    "cus_id": order_data[0],
                    "customer_name": order_data[1],
                    "phone_number": order_data[2],
                    "address": order_data[3]
                },
                "products": []
            }
            
            # Add all products for this order
            for order in orders:
                response_data["products"].append({
                    "prod_id": order[7],
                    "prod_name": order[8],
                    "order_weight": order[9],
                    "order_amount": order[10],
                    "product_sell_price": order[11],
                    "product_labor_cost": order[12],
                    "product_buy_price": order[13],
                    "item_profit": order[10] - ((order[12] or 0) + (order[13] or 0))
                })
            
            return ResponseModel(
                code=200,
                status="Success",
                message=f"Order {order_id} retrieved successfully.",
                result=response_data
            )
        
        else:
            # Multiple orders response - grouped by customer
            order_list = {}
            
            for order in orders:
                cus_id = order[0]
                order_id_current = order[4]

                if cus_id not in order_list:
                    order_list[cus_id] = {
                        "cus_id": cus_id,
                        "customer_name": order[1],
                        "phone_number": order[2],
                        "address": order[3],
                        "orders": {}
                    }

                # Group products by order_id within each customer
                if order_id_current not in order_list[cus_id]["orders"]:
                    order_list[cus_id]["orders"][order_id_current] = {
                        "order_id": order_id_current,
                        "order_deposit": order[5],
                        "order_date": order[6].strftime("%Y-%m-%d %H:%M:%S"),
                        "products": [],
                        "order_total": 0
                    }

                # Add product to the specific order
                product_data = {
                    "prod_id": order[7],
                    "prod_name": order[8],
                    "order_weight": order[9],
                    "order_amount": order[10],
                    "product_sell_price": order[11],
                    "product_labor_cost": order[12],
                    "product_buy_price": order[13],
                    "item_profit": order[10] - ((order[12] or 0) + (order[13] or 0))
                }
                
                order_list[cus_id]["orders"][order_id_current]["products"].append(product_data)
                order_list[cus_id]["orders"][order_id_current]["order_total"] += order[10]

            # Convert nested dict structure to list format
            result = []
            for customer_data in order_list.values():
                customer_data["orders"] = list(customer_data["orders"].values())
                result.append(customer_data)

            return ResponseModel(
                code=200,
                status="Success",
                message=f"Retrieved {len(result)} customers with orders.",
                result=result
            )
