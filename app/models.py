from sqlalchemy import Column, Integer, String, Float
from .database import Base

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String, nullable=True)                # Número de pedido Shopify
    pharmacy_vendor = Column(String, nullable=True)         # Farmacia (vendor del producto)
    product_name = Column(String, nullable=True)
    product_description = Column(String, nullable=True)
    price = Column(Float, nullable=True)
    purchase_date = Column(String, nullable=True)
    customer_name = Column(String, nullable=True)
    customer_country = Column(String, nullable=True)
    customer_phone = Column(String, nullable=True)          # 📌 Teléfono del cliente
    shipping_status = Column(String, nullable=True)
    shipping_address = Column(String, nullable=True)
    billing_address = Column(String, nullable=True)
    customer_email = Column(String, nullable=True)
    quantity = Column(Integer, nullable=True)
    payment_method = Column(String, nullable=True)
    product_id = Column(Integer, nullable=True)
    customer_id = Column(Integer, nullable=True)
    inventory_left = Column(Integer, nullable=True)