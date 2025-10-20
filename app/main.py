from fastapi import FastAPI, Request, Depends, Form, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from . import models, database
import os
from itsdangerous import URLSafeTimedSerializer

app = FastAPI()

# Crear tablas si no existen
models.Base.metadata.create_all(bind=database.engine)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "static"))

# 🔐 Configuración de seguridad para sesiones
SECRET_KEY = "4sjl4YTA6d9neuigDwa_jw8YSzCsHMAgR94pV8AJVAA"  # ⚠️ CAMBIA ESTO EN PRODUCCIÓN
serializer = URLSafeTimedSerializer(SECRET_KEY)

# 🏥 Códigos de acceso por farmacia (vendor name de Shopify)
PHARMACY_CODES = {
    "Farma Leal": "123",
    "Farmacia Alivio": "456",
    "Farmacia Batres": "789",
    "Farmacia Brasil": "111",
    "Farmacia Carol": "222",
    "FarmaGo": "333",
    "Farmacia Medikit": "444",
    "Farmacia PuntoFarma": "555",
    "FARMACIAS VIDA": "666",
    "Farmaconal": "777",
    "FARMAVALUE": "888",
    "JI Cohen": "999",
    "Laboratorio Examedi": "000",
    "LEVIC": "001",
    # Agrega más farmacias según necesites
}

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 🔐 Función para verificar autenticación
def get_current_pharmacy(request: Request) -> str:
    """Obtiene la farmacia autenticada desde la cookie"""
    token = request.cookies.get("pharmacy_session")
    if not token:
        return None
    try:
        # Verificar token (válido por 24 horas)
        pharmacy = serializer.loads(token, max_age=86400)
        return pharmacy
    except:
        return None

# 🔐 Middleware de autenticación
def require_auth(request: Request):
    """Verifica que el usuario esté autenticado"""
    pharmacy = get_current_pharmacy(request)
    if not pharmacy:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    return pharmacy

# 📌 Página de LOGIN
@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    """Muestra el formulario de login"""
    pharmacy = get_current_pharmacy(request)
    if pharmacy:
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse("login.html", {"request": request, "error": None})

# 📌 Procesar LOGIN
@app.post("/login", response_class=HTMLResponse)
def login_submit(request: Request, codigo: str = Form(...)):
    """Procesa el código de acceso"""
    # Buscar farmacia por código
    pharmacy_name = None
    for pharmacy, code in PHARMACY_CODES.items():
        if code == codigo:
            pharmacy_name = pharmacy
            break
    
    if not pharmacy_name:
        return templates.TemplateResponse("login.html", {
            "request": request, 
            "error": "Código incorrecto. Intenta de nuevo."
        })
    
    # Crear token de sesión
    token = serializer.dumps(pharmacy_name)
    
    # Redirigir con cookie
    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    response.set_cookie(
        key="pharmacy_session",
        value=token,
        httponly=True,
        max_age=86400,  # 24 horas
        samesite="lax"
    )
    return response

# 📌 LOGOUT
@app.get("/logout")
def logout():
    """Cierra sesión"""
    response = RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    response.delete_cookie("pharmacy_session")
    return response

# 📌 Página principal (PROTEGIDA)
@app.get("/", response_class=HTMLResponse)
def read_root(request: Request, db: Session = Depends(get_db)):
    # Verificar autenticación
    pharmacy = get_current_pharmacy(request)
    if not pharmacy:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    # 🔍 Filtrar solo pedidos de esta farmacia
    orders = db.query(models.Order).filter_by(pharmacy_vendor=pharmacy).all()
    
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "orders": orders,
        "pharmacy_name": pharmacy  # Para mostrar en la interfaz
    })

# 📌 Webhook Shopify (SIN PROTECCIÓN - debe ser público)
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
                existing_order.inventory_left = None
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
                    customer_phone=shipping.get("phone"),
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