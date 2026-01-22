"""
API service for sales dashboard reminders.
Provides HTTP endpoints for business insights that can be consumed by assistants.
"""
import os
import sys
from datetime import datetime, timedelta
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import uvicorn
import requests
import shutil

# Add the src directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_loader import load_data

app = FastAPI(
    title="Dashboard Ventas API",
    description="API para recordatorios e insights de negocio",
    version="1.0.0"
)

# Enable CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Path relative to src/ directory
DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "source.csv")

# N8N Webhook Configuration (production URL - workflow must be active)
N8N_WEBHOOK_URL = "https://em-n8n.yny2jy.easypanel.host/webhook/1ab642e1-0cfc-48ca-a5b9-4f8ccfefca2c"

def get_df():
    """Load and return the dataframe."""
    return load_data(DATA_PATH)


@app.get("/")
def root():
    """API health check."""
    return {"status": "ok", "message": "Dashboard Ventas API"}


@app.post("/api/upload-data")
async def upload_data(file: UploadFile = File(...)):
    """
    Upload a new CSV file to update the dashboard data.
    """
    try:
        # Determine strict path
        save_path = DATA_PATH
        
        # Save the uploaded file
        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        return {"success": True, "message": f"Archivo actualizado en {save_path}"}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/push-to-n8n")
def push_to_n8n():

    """Push comprehensive reminders to n8n webhook."""
    df = get_df()
    today = df['fecha'].max()
    current_month = today.month
    current_year = today.year
    
    # --- TOP 40 CLIENTES (ordenados por días sin comprar ASC, primero los de 90+ días) ---
    cust_stats = df.groupby('cliente_nombre').agg({
        'venta_neta': 'sum',
        'fecha': ['max', 'count'],
        'cantidad': 'sum'
    }).reset_index()
    cust_stats.columns = ['cliente', 'total_ventas', 'ultima_compra', 'transacciones', 'cantidad']
    cust_stats['dias_sin_compra'] = (today - cust_stats['ultima_compra']).dt.days
    
    # Filtrar clientes importantes (>5 transacciones O >5000 en ventas)
    clientes_importantes = cust_stats[(cust_stats['transacciones'] > 5) | (cust_stats['total_ventas'] > 5000)]
    
    # Ordenar por días ascendente (90, 91, 92...)
    clientes_inactivos = clientes_importantes[clientes_importantes['dias_sin_compra'] >= 90].sort_values('dias_sin_compra', ascending=True).head(40)
    
    clientes_list = []
    for _, row in clientes_inactivos.iterrows():
        clientes_list.append({
            'cliente': row['cliente'],
            'dias_sin_compra': int(row['dias_sin_compra']),
            'total_ventas': round(row['total_ventas'], 2),
            'transacciones': int(row['transacciones']),
            'ultima_compra': row['ultima_compra'].strftime('%Y-%m-%d')
        })
    
    # --- TOP 40 PRODUCTOS (ordenados por días sin vender ASC) ---
    prod_stats = df.groupby('producto').agg({
        'venta_neta': 'sum',
        'fecha': ['max', 'count'],
        'cantidad': 'sum'
    }).reset_index()
    prod_stats.columns = ['producto', 'total_ventas', 'ultima_venta', 'transacciones', 'cantidad']
    prod_stats['dias_sin_venta'] = (today - prod_stats['ultima_venta']).dt.days
    
    # Filtrar productos importantes (>10 transacciones O >5000 en ventas)
    productos_importantes = prod_stats[(prod_stats['transacciones'] > 10) | (prod_stats['total_ventas'] > 5000)]
    
    # Ordenar por días ascendente
    productos_sin_venta = productos_importantes[productos_importantes['dias_sin_venta'] >= 60].sort_values('dias_sin_venta', ascending=True).head(40)
    
    productos_list = []
    for _, row in productos_sin_venta.iterrows():
        productos_list.append({
            'producto': row['producto'],
            'dias_sin_venta': int(row['dias_sin_venta']),
            'total_ventas': round(row['total_ventas'], 2),
            'transacciones': int(row['transacciones']),
            'ultima_venta': row['ultima_venta'].strftime('%Y-%m-%d')
        })
    
    # --- CLIENTES QUE ACABAN DE COMPRAR (últimos 7 días, top ventas) ---
    clientes_recientes = clientes_importantes[clientes_importantes['dias_sin_compra'] <= 7].sort_values('total_ventas', ascending=False).head(15)
    recientes_clientes = []
    for _, row in clientes_recientes.iterrows():
        recientes_clientes.append({
            'cliente': row['cliente'],
            'dias_sin_compra': int(row['dias_sin_compra']),
            'total_ventas': round(row['total_ventas'], 2)
        })
    
    # --- PRODUCTOS QUE ACABAN DE SALIR (últimos 7 días, top ventas) ---
    productos_recientes = productos_importantes[productos_importantes['dias_sin_venta'] <= 7].sort_values('total_ventas', ascending=False).head(15)
    recientes_productos = []
    for _, row in productos_recientes.iterrows():
        recientes_productos.append({
            'producto': row['producto'],
            'dias_sin_venta': int(row['dias_sin_venta']),
            'total_ventas': round(row['total_ventas'], 2)
        })
    
    # --- TOP CLIENTES SIN IMPORTAR FECHA (los que más compran en total) ---
    top_clientes_siempre = clientes_importantes.nlargest(20, 'total_ventas')
    top_clientes_list = []
    for _, row in top_clientes_siempre.iterrows():
        top_clientes_list.append({
            'cliente': row['cliente'],
            'total_ventas': round(row['total_ventas'], 2),
            'transacciones': int(row['transacciones']),
            'dias_sin_compra': int(row['dias_sin_compra'])
        })
    
    # --- TOP PRODUCTOS SIN IMPORTAR FECHA ---
    top_productos_siempre = productos_importantes.nlargest(20, 'total_ventas')
    top_productos_list = []
    for _, row in top_productos_siempre.iterrows():
        top_productos_list.append({
            'producto': row['producto'],
            'total_ventas': round(row['total_ventas'], 2),
            'transacciones': int(row['transacciones']),
            'dias_sin_venta': int(row['dias_sin_venta'])
        })
    
    # --- VENTAS MENSUALES - COMPARACIÓN 3 MESES ---
    def get_month_num(current, offset):
        m = current - offset
        if m <= 0:
            m += 12
        return m
    
    mes_actual = current_month
    mes_anterior = get_month_num(current_month, 1)
    mes_anterior_2 = get_month_num(current_month, 2)
    
    df_mes_actual = df[df['fecha'].dt.month == mes_actual]
    df_mes_ant1 = df[df['fecha'].dt.month == mes_anterior]
    df_mes_ant2 = df[df['fecha'].dt.month == mes_anterior_2]
    
    # --- COMPARACIÓN DE CLIENTES (3 MESES) ---
    clientes_m0 = df_mes_actual.groupby('cliente_nombre')['venta_neta'].sum().nlargest(20).reset_index()
    clientes_m0.columns = ['cliente', 'mes_actual']
    clientes_m1 = df_mes_ant1.groupby('cliente_nombre')['venta_neta'].sum().reset_index()
    clientes_m1.columns = ['cliente', 'mes_anterior']
    clientes_m2 = df_mes_ant2.groupby('cliente_nombre')['venta_neta'].sum().reset_index()
    clientes_m2.columns = ['cliente', 'hace_2_meses']
    
    comp_clientes = clientes_m0.merge(clientes_m1, on='cliente', how='left').merge(clientes_m2, on='cliente', how='left').fillna(0)
    comp_clientes['cambio_vs_anterior'] = comp_clientes['mes_actual'] - comp_clientes['mes_anterior']
    comp_clientes['cambio_vs_hace_2'] = comp_clientes['mes_actual'] - comp_clientes['hace_2_meses']
    comparacion_clientes_list = comp_clientes.round(2).to_dict('records')
    
    # --- COMPARACIÓN DE PRODUCTOS (3 MESES) ---
    prods_m0 = df_mes_actual.groupby('producto')['venta_neta'].sum().nlargest(20).reset_index()
    prods_m0.columns = ['producto', 'mes_actual']
    prods_m1 = df_mes_ant1.groupby('producto')['venta_neta'].sum().reset_index()
    prods_m1.columns = ['producto', 'mes_anterior']
    prods_m2 = df_mes_ant2.groupby('producto')['venta_neta'].sum().reset_index()
    prods_m2.columns = ['producto', 'hace_2_meses']
    
    comp_productos = prods_m0.merge(prods_m1, on='producto', how='left').merge(prods_m2, on='producto', how='left').fillna(0)
    comp_productos['cambio_vs_anterior'] = comp_productos['mes_actual'] - comp_productos['mes_anterior']
    comp_productos['cambio_vs_hace_2'] = comp_productos['mes_actual'] - comp_productos['hace_2_meses']
    comparacion_productos_list = comp_productos.round(2).to_dict('records')
    
    # --- RESULTADO COMPLETO ---
    result = {
        "fecha_generacion": datetime.now().isoformat(),
        "periodo_datos": {
            "desde": df['fecha'].min().strftime('%Y-%m-%d'),
            "hasta": df['fecha'].max().strftime('%Y-%m-%d')
        },
        "meta_ventas_mes": get_monthly_comparison_data(df, today),
        
        "clientes_inactivos_40": {
            "descripcion": "Top 40 clientes importantes sin comprar >=90 días, ordenados por días (asc)",
            "total": len(clientes_list),
            "lista": clientes_list
        },
        
        "productos_sin_movimiento_40": {
            "descripcion": "Top 40 productos importantes sin vender >=60 días, ordenados por días (asc)",
            "total": len(productos_list),
            "lista": productos_list
        },
        
        "clientes_recientes": {
            "descripcion": "Clientes que compraron en los últimos 7 días (top por ventas totales)",
            "lista": recientes_clientes
        },
        
        "productos_recientes": {
            "descripcion": "Productos vendidos en los últimos 7 días (top por ventas totales)",
            "lista": recientes_productos
        },
        
        "top_clientes_historico": {
            "descripcion": "Top 20 clientes por ventas totales (sin importar fecha)",
            "lista": top_clientes_list
        },
        
        "top_productos_historico": {
            "descripcion": "Top 20 productos por ventas totales (sin importar fecha)",
            "lista": top_productos_list
        },
        
        "comparacion_mensual_clientes": {
            "descripcion": "Top 20 clientes - comparación 3 meses (mes actual, anterior, hace 2 meses)",
            "meses": {"actual": mes_actual, "anterior": mes_anterior, "hace_2": mes_anterior_2},
            "lista": comparacion_clientes_list
        },
        
        "comparacion_mensual_productos": {
            "descripcion": "Top 20 productos - comparación 3 meses (mes actual, anterior, hace 2 meses)",
            "meses": {"actual": mes_actual, "anterior": mes_anterior, "hace_2": mes_anterior_2},
            "lista": comparacion_productos_list
        },
        
        "resumen_ejecutivo": generate_executive_summary(df, today)
    }
    
    try:
        # Use POST with JSON body
        response = requests.post(N8N_WEBHOOK_URL, json=result, timeout=60, headers={"Content-Type": "application/json"})
        return {
            "success": True,
            "message": "Datos enviados a n8n exitosamente",
            "n8n_status_code": response.status_code,
            "n8n_response": response.text[:500] if response.text else None,
            "data_preview": {
                "clientes_inactivos": len(clientes_list),
                "productos_sin_movimiento": len(productos_list),
                "clientes_recientes": len(recientes_clientes),
                "productos_recientes": len(recientes_productos)
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@app.get("/api/reminders")
def get_all_reminders():
    """Get all business reminders - SAME DATA as push-to-n8n webhook."""
    df = get_df()
    today = df['fecha'].max()
    current_month = today.month
    current_year = today.year
    
    # --- TOP 40 CLIENTES (ordenados por días sin comprar ASC, primero los de 90+ días) ---
    cust_stats = df.groupby('cliente_nombre').agg({
        'venta_neta': 'sum',
        'fecha': ['max', 'count'],
        'cantidad': 'sum'
    }).reset_index()
    cust_stats.columns = ['cliente', 'total_ventas', 'ultima_compra', 'transacciones', 'cantidad']
    cust_stats['dias_sin_compra'] = (today - cust_stats['ultima_compra']).dt.days
    
    # Filtrar clientes importantes (>5 transacciones O >5000 en ventas)
    clientes_importantes = cust_stats[(cust_stats['transacciones'] > 5) | (cust_stats['total_ventas'] > 5000)]
    
    # Ordenar por días ascendente (90, 91, 92...)
    clientes_inactivos = clientes_importantes[clientes_importantes['dias_sin_compra'] >= 90].sort_values('dias_sin_compra', ascending=True).head(40)
    
    clientes_list = []
    for _, row in clientes_inactivos.iterrows():
        clientes_list.append({
            'cliente': row['cliente'],
            'dias_sin_compra': int(row['dias_sin_compra']),
            'total_ventas': round(row['total_ventas'], 2),
            'transacciones': int(row['transacciones']),
            'ultima_compra': row['ultima_compra'].strftime('%Y-%m-%d')
        })
    
    # --- TOP 40 PRODUCTOS (ordenados por días sin vender ASC) ---
    prod_stats = df.groupby('producto').agg({
        'venta_neta': 'sum',
        'fecha': ['max', 'count'],
        'cantidad': 'sum'
    }).reset_index()
    prod_stats.columns = ['producto', 'total_ventas', 'ultima_venta', 'transacciones', 'cantidad']
    prod_stats['dias_sin_venta'] = (today - prod_stats['ultima_venta']).dt.days
    
    # Filtrar productos importantes (>10 transacciones O >5000 en ventas)
    productos_importantes = prod_stats[(prod_stats['transacciones'] > 10) | (prod_stats['total_ventas'] > 5000)]
    
    # Ordenar por días ascendente
    productos_sin_venta = productos_importantes[productos_importantes['dias_sin_venta'] >= 60].sort_values('dias_sin_venta', ascending=True).head(40)
    
    productos_list = []
    for _, row in productos_sin_venta.iterrows():
        productos_list.append({
            'producto': row['producto'],
            'dias_sin_venta': int(row['dias_sin_venta']),
            'total_ventas': round(row['total_ventas'], 2),
            'transacciones': int(row['transacciones']),
            'ultima_venta': row['ultima_venta'].strftime('%Y-%m-%d')
        })
    
    # --- CLIENTES QUE ACABAN DE COMPRAR (últimos 7 días, top ventas) ---
    clientes_recientes = clientes_importantes[clientes_importantes['dias_sin_compra'] <= 7].sort_values('total_ventas', ascending=False).head(15)
    recientes_clientes = []
    for _, row in clientes_recientes.iterrows():
        recientes_clientes.append({
            'cliente': row['cliente'],
            'dias_sin_compra': int(row['dias_sin_compra']),
            'total_ventas': round(row['total_ventas'], 2)
        })
    
    # --- PRODUCTOS QUE ACABAN DE SALIR (últimos 7 días, top ventas) ---
    productos_recientes = productos_importantes[productos_importantes['dias_sin_venta'] <= 7].sort_values('total_ventas', ascending=False).head(15)
    recientes_productos = []
    for _, row in productos_recientes.iterrows():
        recientes_productos.append({
            'producto': row['producto'],
            'dias_sin_venta': int(row['dias_sin_venta']),
            'total_ventas': round(row['total_ventas'], 2)
        })
    
    # --- TOP CLIENTES SIN IMPORTAR FECHA (los que más compran en total) ---
    top_clientes_siempre = clientes_importantes.nlargest(20, 'total_ventas')
    top_clientes_list = []
    for _, row in top_clientes_siempre.iterrows():
        top_clientes_list.append({
            'cliente': row['cliente'],
            'total_ventas': round(row['total_ventas'], 2),
            'transacciones': int(row['transacciones']),
            'dias_sin_compra': int(row['dias_sin_compra'])
        })
    
    # --- TOP PRODUCTOS SIN IMPORTAR FECHA ---
    top_productos_siempre = productos_importantes.nlargest(20, 'total_ventas')
    top_productos_list = []
    for _, row in top_productos_siempre.iterrows():
        top_productos_list.append({
            'producto': row['producto'],
            'total_ventas': round(row['total_ventas'], 2),
            'transacciones': int(row['transacciones']),
            'dias_sin_venta': int(row['dias_sin_venta'])
        })
    
    # --- VENTAS MENSUALES - COMPARACIÓN 3 MESES ---
    def get_month_num(current, offset):
        m = current - offset
        if m <= 0:
            m += 12
        return m
    
    mes_actual = current_month
    mes_anterior = get_month_num(current_month, 1)
    mes_anterior_2 = get_month_num(current_month, 2)
    
    df_mes_actual = df[df['fecha'].dt.month == mes_actual]
    df_mes_ant1 = df[df['fecha'].dt.month == mes_anterior]
    df_mes_ant2 = df[df['fecha'].dt.month == mes_anterior_2]
    
    # --- COMPARACIÓN DE CLIENTES (3 MESES) ---
    clientes_m0 = df_mes_actual.groupby('cliente_nombre')['venta_neta'].sum().nlargest(20).reset_index()
    clientes_m0.columns = ['cliente', 'mes_actual']
    clientes_m1 = df_mes_ant1.groupby('cliente_nombre')['venta_neta'].sum().reset_index()
    clientes_m1.columns = ['cliente', 'mes_anterior']
    clientes_m2 = df_mes_ant2.groupby('cliente_nombre')['venta_neta'].sum().reset_index()
    clientes_m2.columns = ['cliente', 'hace_2_meses']
    
    comp_clientes = clientes_m0.merge(clientes_m1, on='cliente', how='left').merge(clientes_m2, on='cliente', how='left').fillna(0)
    comp_clientes['cambio_vs_anterior'] = comp_clientes['mes_actual'] - comp_clientes['mes_anterior']
    comp_clientes['cambio_vs_hace_2'] = comp_clientes['mes_actual'] - comp_clientes['hace_2_meses']
    comparacion_clientes_list = comp_clientes.round(2).to_dict('records')
    
    # --- COMPARACIÓN DE PRODUCTOS (3 MESES) ---
    prods_m0 = df_mes_actual.groupby('producto')['venta_neta'].sum().nlargest(20).reset_index()
    prods_m0.columns = ['producto', 'mes_actual']
    prods_m1 = df_mes_ant1.groupby('producto')['venta_neta'].sum().reset_index()
    prods_m1.columns = ['producto', 'mes_anterior']
    prods_m2 = df_mes_ant2.groupby('producto')['venta_neta'].sum().reset_index()
    prods_m2.columns = ['producto', 'hace_2_meses']
    
    comp_productos = prods_m0.merge(prods_m1, on='producto', how='left').merge(prods_m2, on='producto', how='left').fillna(0)
    comp_productos['cambio_vs_anterior'] = comp_productos['mes_actual'] - comp_productos['mes_anterior']
    comp_productos['cambio_vs_hace_2'] = comp_productos['mes_actual'] - comp_productos['hace_2_meses']
    comparacion_productos_list = comp_productos.round(2).to_dict('records')
    
    # --- RESULTADO COMPLETO (MISMO QUE WEBHOOK) ---
    result = {
        "fecha_generacion": datetime.now().isoformat(),
        "periodo_datos": {
            "desde": df['fecha'].min().strftime('%Y-%m-%d'),
            "hasta": df['fecha'].max().strftime('%Y-%m-%d')
        },
        "meta_ventas_mes": get_monthly_comparison_data(df, today),
        
        "clientes_inactivos_40": {
            "descripcion": "Top 40 clientes importantes sin comprar >=90 días, ordenados por días (asc)",
            "total": len(clientes_list),
            "lista": clientes_list
        },
        
        "productos_sin_movimiento_40": {
            "descripcion": "Top 40 productos importantes sin vender >=60 días, ordenados por días (asc)",
            "total": len(productos_list),
            "lista": productos_list
        },
        
        "clientes_recientes": {
            "descripcion": "Clientes que compraron en los últimos 7 días (top por ventas totales)",
            "lista": recientes_clientes
        },
        
        "productos_recientes": {
            "descripcion": "Productos vendidos en los últimos 7 días (top por ventas totales)",
            "lista": recientes_productos
        },
        
        "top_clientes_historico": {
            "descripcion": "Top 20 clientes por ventas totales (sin importar fecha)",
            "lista": top_clientes_list
        },
        
        "top_productos_historico": {
            "descripcion": "Top 20 productos por ventas totales (sin importar fecha)",
            "lista": top_productos_list
        },
        
        "comparacion_mensual_clientes": {
            "descripcion": "Top 20 clientes - comparación 3 meses (mes actual, anterior, hace 2 meses)",
            "meses": {"actual": mes_actual, "anterior": mes_anterior, "hace_2": mes_anterior_2},
            "lista": comparacion_clientes_list
        },
        
        "comparacion_mensual_productos": {
            "descripcion": "Top 20 productos - comparación 3 meses (mes actual, anterior, hace 2 meses)",
            "meses": {"actual": mes_actual, "anterior": mes_anterior, "hace_2": mes_anterior_2},
            "lista": comparacion_productos_list
        },
        
        "resumen_ejecutivo": generate_executive_summary(df, today)
    }
    
    return result


@app.get("/api/reminders/meta-ventas")
def get_monthly_target():
    """Get sales comparison with previous years for current month."""
    df = get_df()
    today = df['fecha'].max()
    return get_monthly_comparison_data(df, today)


@app.get("/api/reminders/clientes-inactivos")
def get_inactive_customers():
    """Get list of customers who haven't purchased in >90 days."""
    df = get_df()
    today = df['fecha'].max()
    return get_inactive_customers_data(df, today)


@app.get("/api/reminders/productos-sin-movimiento")
def get_stale_products():
    """Get top-selling products that haven't sold recently."""
    df = get_df()
    today = df['fecha'].max()
    return get_stale_products_data(df, today)


# --- Helper Functions ---

def get_monthly_comparison_data(df, today):
    """Calculate sales comparison with previous years for current month."""
    current_month = today.month
    current_year = today.year
    
    # Sales by year for current month
    df_month = df[df['fecha'].dt.month == current_month].copy()
    yearly_sales = df_month.groupby(df_month['fecha'].dt.year).agg({
        'venta_neta': 'sum',
        'factura_id': 'nunique',
        'cantidad': 'sum'
    }).reset_index()
    yearly_sales.columns = ['año', 'ventas', 'transacciones', 'cantidad']
    yearly_sales = yearly_sales.sort_values('año', ascending=False)
    
    # Calculate averages and targets
    historical = yearly_sales[yearly_sales['año'] < current_year]
    current = yearly_sales[yearly_sales['año'] == current_year]
    
    avg_sales = historical['ventas'].mean() if not historical.empty else 0
    max_sales = historical['ventas'].max() if not historical.empty else 0
    current_sales = current['ventas'].sum() if not current.empty else 0
    
    # Days elapsed in month vs total days
    days_in_month = (today.replace(month=today.month % 12 + 1, day=1) - timedelta(days=1)).day if today.month < 12 else 31
    days_elapsed = today.day
    projected_sales = (current_sales / days_elapsed * days_in_month) if days_elapsed > 0 else 0
    
    return {
        "mes_actual": today.strftime('%B'),
        "numero_mes": current_month,
        "año_actual": current_year,
        "ventas_actuales": round(current_sales, 2),
        "dias_transcurridos": days_elapsed,
        "dias_en_mes": days_in_month,
        "ventas_proyectadas": round(projected_sales, 2),
        "promedio_historico": round(avg_sales, 2),
        "maximo_historico": round(max_sales, 2),
        "meta_sugerida": round(avg_sales * 1.1, 2),  # 10% above average
        "porcentaje_meta": round((current_sales / avg_sales * 100), 1) if avg_sales > 0 else 0,
        "historico_por_año": yearly_sales.to_dict('records')
    }


def get_inactive_customers_data(df, today, days_threshold=90):
    """Get customers who haven't purchased in X days."""
    # Get customer stats
    cust_stats = df.groupby('cliente_nombre').agg({
        'venta_neta': 'sum',
        'fecha': ['max', 'count'],
        'cantidad': 'sum'
    }).reset_index()
    cust_stats.columns = ['cliente', 'total_ventas', 'ultima_compra', 'transacciones', 'cantidad']
    
    cust_stats['dias_sin_compra'] = (today - cust_stats['ultima_compra']).dt.days
    
    # Filter relevant clients (with significant history)
    relevant = cust_stats[(cust_stats['transacciones'] > 3) | (cust_stats['total_ventas'] > 5000)]
    inactive = relevant[relevant['dias_sin_compra'] > days_threshold].sort_values('total_ventas', ascending=False)
    
    # Calculate potential lost revenue
    potential_lost = inactive['total_ventas'].sum()
    
    inactive_list = inactive.head(20).to_dict('records')
    for item in inactive_list:
        item['ultima_compra'] = item['ultima_compra'].strftime('%Y-%m-%d')
        item['total_ventas'] = round(item['total_ventas'], 2)
    
    return {
        "umbral_dias": days_threshold,
        "clientes_inactivos_total": len(inactive),
        "valor_en_riesgo": round(potential_lost, 2),
        "clientes_prioritarios": inactive_list
    }


def get_stale_products_data(df, today, days_threshold=60):
    """Get top-selling products that haven't sold recently."""
    # Get product stats
    prod_stats = df.groupby('producto').agg({
        'venta_neta': 'sum',
        'fecha': ['max', 'count'],
        'cantidad': 'sum'
    }).reset_index()
    prod_stats.columns = ['producto', 'total_ventas', 'ultima_venta', 'transacciones', 'cantidad']
    
    prod_stats['dias_sin_venta'] = (today - prod_stats['ultima_venta']).dt.days
    
    # Top products by historical sales
    top_products = prod_stats.nlargest(50, 'total_ventas')
    
    # Filter those that haven't sold recently
    stale = top_products[top_products['dias_sin_venta'] > days_threshold].sort_values('total_ventas', ascending=False)
    
    stale_list = stale.to_dict('records')
    for item in stale_list:
        item['ultima_venta'] = item['ultima_venta'].strftime('%Y-%m-%d')
        item['total_ventas'] = round(item['total_ventas'], 2)
    
    return {
        "umbral_dias": days_threshold,
        "productos_afectados": len(stale),
        "productos": stale_list
    }


def generate_executive_summary(df, today):
    """Generate an executive summary text for the assistant."""
    meta = get_monthly_comparison_data(df, today)
    inactive = get_inactive_customers_data(df, today)
    stale = get_stale_products_data(df, today)
    
    summary_parts = []
    
    # Sales target status
    if meta['porcentaje_meta'] < 80:
        summary_parts.append(
            f"⚠️ ALERTA: Las ventas de {meta['mes_actual']} están al {meta['porcentaje_meta']}% de la meta. "
            f"Ventas actuales: ${meta['ventas_actuales']:,.0f}, Meta: ${meta['meta_sugerida']:,.0f}."
        )
    elif meta['porcentaje_meta'] >= 100:
        summary_parts.append(
            f"✅ EXCELENTE: Las ventas de {meta['mes_actual']} superan la meta ({meta['porcentaje_meta']}%). "
            f"Ventas: ${meta['ventas_actuales']:,.0f}."
        )
    else:
        summary_parts.append(
            f"📊 Las ventas de {meta['mes_actual']} están al {meta['porcentaje_meta']}% de la meta. "
            f"Faltan ${meta['meta_sugerida'] - meta['ventas_actuales']:,.0f} para alcanzarla."
        )
    
    # Inactive customers
    if inactive['clientes_inactivos_total'] > 0:
        summary_parts.append(
            f"👥 Hay {inactive['clientes_inactivos_total']} clientes sin comprar en más de 90 días, "
            f"representando ${inactive['valor_en_riesgo']:,.0f} en ventas históricas."
        )
    
    # Stale products
    if stale['productos_afectados'] > 0:
        summary_parts.append(
            f"📦 {stale['productos_afectados']} productos populares no se han vendido en más de 60 días. "
            f"Revisar inventario y promociones."
        )
    
    return " ".join(summary_parts)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8502)
