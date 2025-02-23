from pydantic import BaseModel, Field
from datetime import date
from typing import Optional, List
# from typing import , Optional

class BuyProducts(BaseModel):
    prod_id: Optional[int] = None  
    prod_name: Optional[str] = None
    order_weight: Optional[str] = None
    order_amount: Optional[int] = None
    product_sell_price: Optional[float] = None
    product_labor_cost: Optional[float] = None
    product_buy_price: Optional[float] = None

class CreateClient(BaseModel):
    cus_name: str
    address: str
    phone_number: str
    
class CreateProduct(BaseModel):
    prod_name: str
    unit_price: Optional[float] = None
    amount: Optional[int] = None

class CreateOrder(BaseModel):
    order_id: Optional[int] = None
    cus_id: Optional[int] = None
    cus_name: Optional[str] = None
    address: Optional[str] = None
    phone_number: str  
    order_date: Optional[date] = None  
    order_deposit: Optional[float] = None
    order_product_detail: List[BuyProducts] = Field(default_factory=list)


class GetClient(CreateClient):
    cus_id: int
    
    
class UpdateProduct(BaseModel):
    prod_id: Optional[int] = None
    prod_name: Optional[str] = None
    unit_price: Optional[float] = None
    amount: Optional[int] = None


class PawnProductDetail(BaseModel):
    prod_id: Optional[int] = None
    prod_name: Optional[str] = None
    pawn_weight: Optional[str] = None
    pawn_amount: Optional[int] = None
    pawn_unit_price: Optional[float] = None

class CreatePawn(BaseModel):
    pawn_id: Optional[int] = None 
    cus_id: Optional[int] = 0
    cus_name: Optional[str] = None
    address: Optional[str] = None
    phone_number: str
    pawn_date: Optional[date] = None
    pawn_expire_date: Optional[date] = None
    pawn_deposit: Optional[float] = 0
    # products: List[PawnProducts] = []
    pawn_product_detail: List[PawnProductDetail] = Field(default_factory=list)
    
class UpdatePawn(BaseModel):
    # pawn_id: Optional[int] = None
    cus_id: int
    customer_name: Optional[str] = None
    phone_number: str 
    address: Optional[str] = None
    pawn_deposit: Optional[float] = None
    pawn_date: Optional[date] = None
    pawn_expire_date: Optional[date] = None
    # products: List[PawnProducts] = []
    deleteOldProducts: Optional[bool] = False 
    
