import pandas as pd
import numpy as np
from faker import Faker
import random

fake = Faker('es_CO')
random.seed(42)

# Variables base
clientes = [fake.company() for _ in range(30)]
canales = ['Online', 'Distribuidor', 'Tienda']
productos = ['Laptop', 'Tablet', 'Router', 'Switch', 'Impresora']
materiales = [f'MAT{1000+i}' for i in range(len(productos))]
monedas = ['COP', 'USD']

# 1. Ventas
ventas = []
for _ in range(200):
    cliente = random.choice(clientes)
    producto = random.choice(productos)
    doc = random.randint(100000, 999999)
    ventas.append([
        doc,
        fake.date_between(start_date='-45d', end_date='today'),
        cliente[:10],
        cliente,
        random.choice(canales),
        producto,
        random.randint(1, 10),
        round(random.uniform(1000, 5000), 2),
        random.choice(monedas)
    ])
df_ventas = pd.DataFrame(ventas, columns=[
    'Doc_Venta', 'Fecha_Doc', 'Cliente', 'Nombre_Cliente', 'Canal',
    'Producto', 'Cantidad', 'Valor_Neto', 'Moneda'
])
df_ventas.to_excel('F_ventas_sap.xlsx', index=False)

# 2. Pagos
pagos = []
for _ in range(120):
    cliente = random.choice(clientes)
    pagos.append([
        random.randint(700000, 799999),
        fake.date_between(start_date='-30d', end_date='today'),
        cliente[:10],
        cliente,
        random.choice(['Bancolombia', 'Davivienda', 'BBVA']),
        round(random.uniform(500, 7000), 2),
        random.choice(monedas),
        random.choice(df_ventas['Doc_Venta'].tolist())
    ])
df_pagos = pd.DataFrame(pagos, columns=[
    'Doc_Pago', 'Fecha_Pago', 'Cliente', 'Nombre_Cliente', 'Banco',
    'Monto_Pago', 'Moneda', 'Referencia_Factura'
])
df_pagos.to_excel('F_pagos_clientes.xlsx', index=False)

# 3. Stock
stock = []
for mat, prod in zip(materiales, productos):
    stock.append([
        mat,
        prod,
        random.choice(['1100', '1200']),
        random.choice(['Z01', 'Z02']),
        random.randint(10, 200),
        'UN'
    ])
df_stock = pd.DataFrame(stock, columns=[
    'Material', 'Descripción', 'Centro', 'Tipo_Almacén', 'Stock_Total', 'Unidad_Medida'
])
df_stock.to_excel('MM_stock_actual.xlsx', index=False)
