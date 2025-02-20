from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Float
from sqlalchemy.orm import relationship
from datetime import datetime

from database import Base

class OrderDetail(Base):
    __tablename__ = "order_details"

    order_id = Column(Integer, ForeignKey("orders.order_id"), primary_key = True)
    prod_id = Column(Integer, ForeignKey("products.prod_id"), primary_key = True)
    order_weight = Column(String, nullable=False)
    order_amount = Column(Integer, nullable=True)
    product_sell_price = Column(Float, nullable=False)
    product_labor_cost = Column(Float, nullable=False)
    product_buy_price = Column(Float, nullable=False)
    order_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    order_detail_order = relationship("Order")
    order_detail_product = relationship("Product")
    
class PawnDetail(Base):
    __tablename__ = "pawn_details"

    pawn_id = Column(Integer, ForeignKey("pawns.pawn_id"), primary_key = True)
    prod_id = Column(Integer, ForeignKey("products.prod_id"), primary_key = True)
    pawn_weight = Column(String, nullable=False)
    pawn_amount = Column(Integer, nullable=False)
    pawn_unit_price = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    pawn_detail_pawn = relationship("Pawn")
    pawn_detail_product = relationship("Product")

class Account(Base):
    __tablename__ = "accounts"

    cus_id = Column(Integer, primary_key = True, index = True)
    cus_name = Column(String, nullable = False)
    address = Column(String, nullable = True)
    phone_number = Column(String, unique = True, nullable = False)
    password = Column(String, nullable = True, default=None)
    role = Column(Enum("admin", "user", name = "role"), default = 'user')
    created_at = Column(DateTime, default = datetime.utcnow, nullable = False)
    updated_at = Column(DateTime, default = datetime.utcnow, onupdate = datetime.utcnow, nullable = False)
    
    account_product = relationship("Product", primaryjoin="Account.cus_id == Product.user_id", back_populates="product_account")
    account_order = relationship("Order", primaryjoin="Account.cus_id == Order.cus_id", back_populates="order_account")
    account_pawn = relationship("Pawn", primaryjoin="Account.cus_id == Pawn.cus_id", back_populates="pawn_account")

class Product(Base):
    __tablename__ = "products"

    prod_id = Column(Integer, primary_key=True, index=True)
    prod_name = Column(String, nullable=False)
    unit_price = Column(Float, nullable=True, default=None)
    amount = Column(Integer, nullable=True, default=None)
    user_id = Column(Integer, ForeignKey("accounts.cus_id"))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True)

    product_account = relationship("Account", foreign_keys=[user_id], back_populates="account_product")
    product_order_detail = relationship("Order", secondary=OrderDetail.__table__, back_populates="order_product_detail")
    product_pawn_detail = relationship("Pawn", secondary=PawnDetail.__table__, back_populates="pawn_product_detail")
    
class Order(Base):
    __tablename__ = "orders"

    order_id = Column(Integer, primary_key=True, index=True)
    cus_id = Column(Integer, ForeignKey("accounts.cus_id"))
    order_deposit = Column(Float, default=0, nullable=False)
    order_date = Column(DateTime, default = datetime.utcnow, nullable = False)
    
    order_account = relationship("Account", foreign_keys=[cus_id], back_populates="account_order")
    order_product_detail = relationship("Product", secondary=OrderDetail.__table__, back_populates="product_order_detail")
    
class Pawn(Base):
    __tablename__ = "pawns"

    pawn_id = Column(Integer, primary_key=True, index=True)
    cus_id = Column(Integer, ForeignKey("accounts.cus_id"))
    pawn_deposit = Column(Float, default=0, nullable=False)
    pawn_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    pawn_expire_date = Column(DateTime, nullable=False)

    pawn_account = relationship("Account", foreign_keys=[cus_id], back_populates="account_pawn")
    pawn_product_detail = relationship("Product", secondary=PawnDetail.__table__, back_populates="product_pawn_detail")
    
    