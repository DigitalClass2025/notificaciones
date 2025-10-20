"""
🧪 SIMULADOR DE WEBHOOKS SHOPIFY
Este archivo genera pedidos de prueba para testear tu sistema SIN necesidad de Shopify

IMPORTANTE: Esto es SOLO para pruebas. Una vez que tengas tu dominio y conectes
Shopify real, puedes eliminar este archivo.

USO:
1. Asegúrate de que tu app esté corriendo (uvicorn)
2. En otra terminal ejecuta: python test_simulator.py
3. Se crearán pedidos de prueba en tu base de datos
"""

import requests
import random
from datetime import datetime, timedelta

# 🔧 CONFIGURACIÓN
API_URL = "http://localhost:8000/webhook/orders"  # Cambia si tu puerto es diferente
# Si ya está en AWS: API_URL = "http://tu-ip-de-aws:8000/webhook/orders"

# 🏥 Farmacias REALES (coinciden con PHARMACY_CODES en main.py)
FARMACIAS = [
    "Farma Leal",
    "Farmacia Alivio", 
    "Farmacia Batres",
    "Farmacia Brasil",
    "Farmacia Carol",
    "FarmaGo",
    "Farmacia Medikit",
    "Farmacia PuntoFarma",
    "FARMACIAS VIDA",
    "Farmaconal",
    "FARMAVALUE",
    "JI Cohen",
    "Laboratorio Examedi",
    "LEVIC"
]

# 📦 Productos de ejemplo
PRODUCTOS = [
    {"name": "Paracetamol 500mg", "title": "Analgésico", "price": "45.00", "id": 12345},
    {"name": "Ibuprofeno 400mg", "title": "Antiinflamatorio", "price": "78.50", "id": 12346},
    {"name": "Amoxicilina 500mg", "title": "Antibiótico", "price": "120.00", "id": 12347},
    {"name": "Loratadina 10mg", "title": "Antihistamínico", "price": "32.00", "id": 12348},
    {"name": "Omeprazol 20mg", "title": "Protector gástrico", "price": "95.00", "id": 12349},
]

# 👤 Clientes de ejemplo
CLIENTES = [
    {"first": "Juan", "last": "Pérez", "email": "juan.perez@email.com", "phone": "+52 55 1234 5678"},
    {"first": "María", "last": "González", "email": "maria.gonzalez@email.com", "phone": "+52 55 8765 4321"},
    {"first": "Carlos", "last": "Rodríguez", "email": "carlos.rodriguez@email.com", "phone": "+52 55 5555 1234"},
    {"first": "Ana", "last": "Martínez", "email": "ana.martinez@email.com", "phone": "+52 55 9876 5432"},
]

# 📍 Direcciones de ejemplo
DIRECCIONES = [
    {
        "address1": "Av. Reforma 123",
        "address2": "Depto 4B",
        "city": "Ciudad de México",
        "province": "CDMX",
        "zip": "06600",
        "country": "Mexico"
    },
    {
        "address1": "Calle Insurgentes 456",
        "address2": None,
        "city": "Guadalajara",
        "province": "Jalisco",
        "zip": "44100",
        "country": "Mexico"
    },
    {
        "address1": "Av. Universidad 789",
        "address2": "Col. Centro",
        "city": "Monterrey",
        "province": "Nuevo León",
        "zip": "64000",
        "country": "Mexico"
    },
]

ESTADOS_ENVIO = [
    {"fulfillment_status": None, "cancelled_at": None},  # En proceso
    {"fulfillment_status": "fulfilled", "cancelled_at": None},  # Entregado
    {"fulfillment_status": "partial", "cancelled_at": None},  # Parcial
    {"fulfillment_status": None, "cancelled_at": "2024-01-15T10:00:00Z"},  # Cancelado
]

METODOS_PAGO = ["Stripe", "PayPal", "Tarjeta de crédito", "Transferencia", "Efectivo"]


def generar_webhook_shopify():
    """Genera un webhook falso que simula uno real de Shopify"""
    
    cliente = random.choice(CLIENTES)
    direccion = random.choice(DIRECCIONES)
    producto = random.choice(PRODUCTOS)
    estado = random.choice(ESTADOS_ENVIO)
    farmacia = random.choice(FARMACIAS)
    
    # Generar fecha aleatoria en los últimos 30 días
    dias_atras = random.randint(0, 30)
    fecha = (datetime.now() - timedelta(days=dias_atras)).isoformat() + "Z"
    
    # ID de pedido único
    order_number = random.randint(1000, 9999)
    
    webhook_data = {
        "order_number": order_number,
        "created_at": fecha,
        "email": cliente["email"],
        "gateway": random.choice(METODOS_PAGO),
        "payment_gateway_names": [random.choice(METODOS_PAGO)],
        "fulfillment_status": estado["fulfillment_status"],
        "cancelled_at": estado["cancelled_at"],
        "customer": {
            "id": random.randint(100000, 999999),
            "first_name": cliente["first"],
            "last_name": cliente["last"]
        },
        "shipping_address": {
            "address1": direccion["address1"],
            "address2": direccion["address2"],
            "city": direccion["city"],
            "province": direccion["province"],
            "zip": direccion["zip"],
            "country": direccion["country"],
            "phone": cliente["phone"]
        },
        "billing_address": direccion.copy(),  # Usar misma dirección para facturación
        "line_items": [
            {
                "product_id": producto["id"],
                "name": producto["name"],
                "title": producto["title"],
                "price": producto["price"],
                "quantity": random.randint(1, 5),
                "vendor": farmacia  # 🏥 IMPORTANTE: Aquí va el nombre de la farmacia
            }
        ]
    }
    
    return webhook_data


def enviar_pedido_prueba(webhook_data):
    """Envía el webhook a tu API local"""
    try:
        response = requests.post(API_URL, json=webhook_data, timeout=5)
        if response.status_code == 200:
            print(f"✅ Pedido #{webhook_data['order_number']} creado - Farmacia: {webhook_data['line_items'][0]['vendor']}")
            return True
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ No se pudo conectar. ¿Está corriendo tu app con 'uvicorn main:app --reload'?")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def menu_principal():
    """Menú interactivo para generar pedidos de prueba"""
    print("\n" + "="*60)
    print("🧪 SIMULADOR DE WEBHOOKS SHOPIFY - MODO PRUEBA")
    print("="*60)
    print(f"\n🌐 Enviando pedidos a: {API_URL}")
    print(f"🏥 Farmacias configuradas: {', '.join(FARMACIAS)}")
    print("\nOpciones:")
    print("  1️⃣  - Crear 1 pedido de prueba")
    print("  2️⃣  - Crear 5 pedidos de prueba")
    print("  3️⃣  - Crear 10 pedidos de prueba")
    print("  4️⃣  - Crear 20 pedidos de prueba")
    print("  5️⃣  - Crear pedido personalizado")
    print("  0️⃣  - Salir")
    print("="*60)


def crear_pedido_personalizado():
    """Permite crear un pedido con datos específicos"""
    print("\n📝 CREAR PEDIDO PERSONALIZADO")
    print("-" * 40)
    
    print("\nFarmacias disponibles:")
    for i, farmacia in enumerate(FARMACIAS, 1):
        print(f"  {i}. {farmacia}")
    
    try:
        idx = int(input(f"\nElige farmacia (1-{len(FARMACIAS)}): ")) - 1
        farmacia = FARMACIAS[idx]
    except:
        print("❌ Opción inválida")
        return
    
    print("\nProductos disponibles:")
    for i, prod in enumerate(PRODUCTOS, 1):
        print(f"  {i}. {prod['name']} - ${prod['price']}")
    
    try:
        idx = int(input(f"\nElige producto (1-{len(PRODUCTOS)}): ")) - 1
        producto = PRODUCTOS[idx]
    except:
        print("❌ Opción inválida")
        return
    
    print("\nEstados de envío:")
    print("  1. En proceso")
    print("  2. Entregado")
    print("  3. Parcialmente enviado")
    print("  4. Cancelado")
    
    try:
        estado_idx = int(input("\nElige estado (1-4): ")) - 1
        estado = ESTADOS_ENVIO[estado_idx]
    except:
        print("❌ Opción inválida")
        return
    
    # Generar webhook
    webhook = generar_webhook_shopify()
    webhook["line_items"][0]["vendor"] = farmacia
    webhook["line_items"][0].update(producto)
    webhook["fulfillment_status"] = estado["fulfillment_status"]
    webhook["cancelled_at"] = estado["cancelled_at"]
    
    print(f"\n🚀 Creando pedido para {farmacia}...")
    enviar_pedido_prueba(webhook)


def main():
    while True:
        menu_principal()
        
        opcion = input("\n👉 Elige una opción: ").strip()
        
        if opcion == "0":
            print("\n👋 ¡Hasta luego! Recuerda eliminar este archivo cuando conectes Shopify real.\n")
            break
        
        cantidad = 0
        if opcion == "1":
            cantidad = 1
        elif opcion == "2":
            cantidad = 5
        elif opcion == "3":
            cantidad = 10
        elif opcion == "4":
            cantidad = 20
        elif opcion == "5":
            crear_pedido_personalizado()
            input("\nPresiona ENTER para continuar...")
            continue
        else:
            print("❌ Opción no válida")
            input("\nPresiona ENTER para continuar...")
            continue
        
        print(f"\n🚀 Creando {cantidad} pedido(s) de prueba...\n")
        
        exitos = 0
        for i in range(cantidad):
            webhook = generar_webhook_shopify()
            if enviar_pedido_prueba(webhook):
                exitos += 1
        
        print(f"\n✨ Resultado: {exitos}/{cantidad} pedidos creados exitosamente")
        input("\nPresiona ENTER para continuar...")


if __name__ == "__main__":
    print("\n🔍 Verificando conexión con tu API...")
    test_webhook = generar_webhook_shopify()
    
    # Intentar una conexión de prueba
    try:
        response = requests.get("http://localhost:8000/", timeout=2)
        print("✅ API detectada en http://localhost:8000")
    except:
        print("⚠️  No se detectó la API en http://localhost:8000")
        print("   Asegúrate de que esté corriendo con: uvicorn main:app --reload")
        print("\n   Si está en AWS, cambia API_URL al inicio de este archivo")
        input("\n   Presiona ENTER para continuar de todos modos...")
    
    main()