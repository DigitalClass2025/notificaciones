from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from . import models, database
import os

app = FastAPI()

# Crear tablas si no existen
models.Base.metadata.create_all(bind=database.engine)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "static"))

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 📌 Página principal
@app.get("/", response_class=HTMLResponse)
def read_root(request: Request, db: Session = Depends(get_db)):
    orders = db.query(models.Order).all()
    return templates.TemplateResponse("index.html", {"request": request, "orders": orders})

# 📌 Webhook Shopify
@app.post("/webhook/orders")
async def webhook_orders(request: Request, db: Session = Depends(get_db)):
    try:
        data = await request.json()

        customer = data.get("customer", {})
        shipping = data.get("shipping_address", {}) or {}
        billing = data.get("billing_address", {}) or {}

        # Dirección completa
        full_shipping = ", ".join(filter(None, [
            shipping.get("address1"),
            shipping.get("address2"),
            shipping.get("city"),
            shipping.get("province"),
            shipping.get("zip"),
            shipping.get("country")
        ]))

        full_billing = ", ".join(filter(None, [
            billing.get("address1"),
            billing.get("address2"),
            billing.get("city"),
            billing.get("province"),
            billing.get("zip"),
            billing.get("country")
        ]))

        # Método de pago
        payment_method = data.get("gateway")
        if not payment_method:
            payment_methods = data.get("payment_gateway_names", [])
            payment_method = payment_methods[0] if payment_methods else "No especificado"

        # Número de pedido (el chiquito de Shopify)
        order_id = str(data.get("order_number"))

        # Estado de envío
        if data.get("cancelled_at"):
            shipping_status = "Cancelado"
        elif data.get("fulfillment_status") == "fulfilled":
            shipping_status = "Entregado"
        elif data.get("fulfillment_status") == "partial":
            shipping_status = "Parcialmente enviado"
        else:
            shipping_status = "En proceso"

        # 📌 Guardar o actualizar por cada producto
        for line_item in data.get("line_items", []):
            # Buscar si ya existe este producto en este pedido
            existing_order = db.query(models.Order).filter_by(
                order_id=order_id,
                product_id=line_item.get("product_id")
            ).first()

            if existing_order:
                # 👉 Actualizar solo los campos que pueden cambiar
                existing_order.shipping_status = shipping_status
                existing_order.inventory_left = None  # Aquí luego puedes actualizar stock si lo necesitas
                db.add(existing_order)
            else:
                # 👉 Crear nuevo si no existe
                order = models.Order(
                    order_id=order_id,
                    pharmacy_vendor=line_item.get("vendor"),  # Farmacia que vende
                    product_name=line_item.get("name"),
                    product_description=line_item.get("title"),
                    price=float(line_item.get("price", 0)),
                    purchase_date=data.get("created_at"),
                    customer_name=f"{customer.get('first_name','')} {customer.get('last_name','')}",
                    customer_country=shipping.get("country"),
                    customer_phone=shipping.get("phone"),  # 📌 Teléfono cliente
                    shipping_status=shipping_status,
                    shipping_address=full_shipping,
                    billing_address=full_billing,
                    customer_email=data.get("email"),
                    quantity=line_item.get("quantity", 1),
                    payment_method=payment_method,
                    product_id=line_item.get("product_id"),
                    customer_id=customer.get("id"),
                    inventory_left=None
                )
                db.add(order)

        db.commit()
        return {"status": "ok"}
    except Exception as e:
        print("Error webhook:", e)
        return {"status": "error", "detail": str(e)}