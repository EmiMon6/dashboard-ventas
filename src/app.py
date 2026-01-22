
import streamlit as st
import pandas as pd
import plotly.express as px
from data_loader import load_data, get_kpis, normalize_products

# Page Configuration
st.set_page_config(
    page_title="Dashboard de Ventas",
    page_icon="bar_chart",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- PASSWORD PROTECTION ---
DASHBOARD_PIN = "101010"

def check_password():
    """Returns True if the user has entered the correct password."""
    
    def password_entered():
        """Checks whether the password is correct."""
        if st.session_state.get("password") == DASHBOARD_PIN:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store password
        else:
            st.session_state["password_correct"] = False
    
    # First run or not authenticated
    if "password_correct" not in st.session_state:
        st.markdown("""
        <style>
        .login-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 60vh;
        }
        .login-title {
            font-size: 2.5rem;
            margin-bottom: 1rem;
            color: #00d4aa;
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown("<div class='login-container'>", unsafe_allow_html=True)
        st.markdown("<p class='login-title'>🔐 Dashboard de Ventas</p>", unsafe_allow_html=True)
        st.text_input(
            "Ingresa el PIN de acceso:",
            type="password",
            on_change=password_entered,
            key="password",
            placeholder="••••••"
        )
        st.markdown("</div>", unsafe_allow_html=True)
        return False
    
    # Wrong password entered
    elif not st.session_state["password_correct"]:
        st.markdown("""
        <style>
        .login-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 60vh;
        }
        .login-title {
            font-size: 2.5rem;
            margin-bottom: 1rem;
            color: #00d4aa;
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown("<div class='login-container'>", unsafe_allow_html=True)
        st.markdown("<p class='login-title'>🔐 Dashboard de Ventas</p>", unsafe_allow_html=True)
        st.text_input(
            "Ingresa el PIN de acceso:",
            type="password",
            on_change=password_entered,
            key="password",
            placeholder="••••••"
        )
        st.error("❌ PIN incorrecto. Intenta de nuevo.")
        st.markdown("</div>", unsafe_allow_html=True)
        return False
    
    # Password correct
    return True

# Check password before showing anything
if not check_password():
    st.stop()

# Custom CSS for Dark/Premium Look
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
    }
    .stMetric {
        background-color: #262730;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #3d3f4b;
    }
    </style>
    """, unsafe_allow_html=True)

# Load Data
import os
# Path relative to src/ directory
DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "source.csv")

df = load_data(DATA_PATH)

if df.empty:
    st.warning(f"No se encontraron datos en {DATA_PATH}. Por favor carga un archivo CSV en la sección de Configuración.")

# Sidebar Navigation
st.sidebar.title("Navegación")
view_options = ["Visión General", "📢 Recordatorios", "Análisis por Categoría", "Categorías Agrupadas", "Análisis de Recencia", "Explorador de Clientes", "Datos Crudos", "⚙️ Configuración"]
selected_view = st.sidebar.radio("Ir a la sección:", view_options)

# Sidebar Filters (Global)
st.sidebar.markdown("---")
st.sidebar.header("Filtros Globales")
min_date = df['fecha'].min()
max_date = df['fecha'].max()

if pd.isnull(min_date) or pd.isnull(max_date):
    st.sidebar.error("Error with date formats in CSV.")
    filtered_df = df
else:
    # Date Presets
    date_preset = st.sidebar.selectbox(
        "Filtro Rápido:",
        ["Todos", "Este Año", "Últimos 6 Meses", "Últimos 3 Meses", "Último Mes", "Última Semana", "Personalizado"]
    )

    if date_preset == "Personalizado":
        date_range = st.sidebar.date_input(
            "Rango de Fechas",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )
    else:
        # Calculate range based on max_date from data
        end_date = max_date
        if date_preset == "Este Año":
            # January 1st of current year to max_date
            start_date = pd.Timestamp(year=max_date.year, month=1, day=1)
        elif date_preset == "Últimos 6 Meses":
            start_date = end_date - pd.DateOffset(months=6)
        elif date_preset == "Últimos 3 Meses":
            start_date = end_date - pd.DateOffset(months=3)
        elif date_preset == "Último Mes":
            start_date = end_date - pd.DateOffset(months=1)
        elif date_preset == "Última Semana":
            start_date = end_date - pd.DateOffset(weeks=1)
        else: # Todos
            start_date = min_date
            
        date_range = (start_date, end_date)
        # Show the range being applied
        st.sidebar.caption(f"Del: {start_date.strftime('%d/%m/%Y')} al {end_date.strftime('%d/%m/%Y')}")
    
    # Apply Filter
    if len(date_range) == 2:
        start_date, end_date = date_range
        # Ensure we compare date objects
        if isinstance(start_date, pd.Timestamp): start_date = start_date.date()
        if isinstance(end_date, pd.Timestamp): end_date = end_date.date()
        
        mask = (df['fecha'].dt.date >= start_date) & (df['fecha'].dt.date <= end_date)
        filtered_df = df.loc[mask]
    else:
        filtered_df = df

# --- VIEW FUNCTIONS ---

def render_overview():
    st.title("📊 Visión General")
    
    # KPIs
    kpis = get_kpis(filtered_df)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Ventas Totales", f"${kpis['total_revenue']:,.2f}")
    c2.metric("Total Pedidos", f"{kpis['total_orders']:,}")
    c3.metric("Unidades Vendidas", f"{kpis['total_items']:,.0f}")
    c4.metric("Ticket Promedio", f"${kpis['avg_order_value']:,.2f}")

    st.markdown("---")

    # Trend and Top Products
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Tendencia de Ventas (Mensual)")
        # Group by Month-Year for the trend line
        filtered_df['mes_anio'] = filtered_df['fecha'].dt.to_period('M').astype(str)
        sales_over_time = filtered_df.groupby('mes_anio')['venta_neta'].sum().reset_index()
        fig_line = px.line(sales_over_time, x='mes_anio', y='venta_neta', title='Ventas Mensuales', template='plotly_dark', markers=True)
        fig_line.update_layout(xaxis_title="Mes", yaxis_title="Ventas ($)")
        st.plotly_chart(fig_line, use_container_width=True)

        # Seasonality Analysis
        st.subheader("Estacionalidad: ¿Cuándo se vende más?")
        filtered_df['nombre_mes'] = filtered_df['fecha'].dt.month_name()
        filtered_df['num_mes'] = filtered_df['fecha'].dt.month
        
        seasonality = filtered_df.groupby(['num_mes', 'nombre_mes'])['venta_neta'].sum().reset_index()
        avg_total = seasonality['venta_neta'].mean()
        seasonality['status'] = seasonality['venta_neta'].apply(
            lambda x: 'Alto' if x > avg_total * 1.1 else ('Bajo' if x < avg_total * 0.9 else 'Normal')
        )
        color_map = {'Alto': '#00cc96', 'Normal': '#636efa', 'Bajo': '#ef553b'}
        
        fig_season = px.bar(seasonality, x='nombre_mes', y='venta_neta', 
                            title='Ventas Totales por Mes (Estacionalidad)',
                            color='status', color_discrete_map=color_map,
                            template='plotly_dark')
        fig_season.update_layout(xaxis={'categoryorder': 'array', 'categoryarray': ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']})
        st.plotly_chart(fig_season, use_container_width=True)

    with col2:
        st.subheader("Top Productos")
        top_products = filtered_df.groupby('producto')['venta_neta'].sum().nlargest(15).reset_index()
        fig_bar = px.bar(top_products, x='venta_neta', y='producto', orientation='h', title='Top Productos por Ingresos', template='plotly_dark', color='venta_neta')
        fig_bar.update_layout(yaxis={'categoryorder': 'total ascending'}, xaxis_title="Ingresos ($)", yaxis_title="Producto")
        st.plotly_chart(fig_bar, use_container_width=True)

    # Categories and Customers
    col3, col4 = st.columns(2)

    with col3:
        st.subheader("Ventas por Categoría")
        if 'categoria' in filtered_df.columns:
            cat_sales = filtered_df.groupby('categoria')['venta_neta'].sum().reset_index()
            fig_pie = px.pie(cat_sales, values='venta_neta', names='categoria', title='Distribución por Categoría', template='plotly_dark')
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Columna 'categoria' no encontrada.")

    with col4:
        st.subheader("Top Clientes")
        top_customers = filtered_df.groupby('cliente_nombre')['venta_neta'].sum().nlargest(10).reset_index()
        fig_cust = px.bar(top_customers, x='cliente_nombre', y='venta_neta', title='Top 10 Clientes', template='plotly_dark')
        st.plotly_chart(fig_cust, use_container_width=True)


def render_recency_analysis():
    st.title("⏳ Análisis de Recencia (Riesgo de Fuga)")
    st.caption("Identifica productos o clientes en riesgo de inactividad (>90 días).")
    
    max_recency_date = df['fecha'].max()

    # 1. Product Recency (Global)
    st.subheader("1. Estado de Productos (Global)")

    prod_stats = df.groupby('producto').agg({
        'venta_neta': 'sum',
        'fecha': 'max'
    }).reset_index()

    prod_stats['dias_sin_venta'] = (max_recency_date - prod_stats['fecha']).dt.days
    prod_stats['estado'] = prod_stats['dias_sin_venta'].apply(lambda x: 'Alerta (>90 días)' if x > 90 else 'Activo')

    fig_prod_recency = px.scatter(
        prod_stats, 
        x='dias_sin_venta', 
        y='venta_neta', 
        color='estado',
        hover_name='producto',
        title='Productos: Ventas vs Días sin Vender',
        color_discrete_map={'Alerta (>90 días)': '#ef553b', 'Activo': '#00cc96'},
        template='plotly_dark'
    )
    fig_prod_recency.add_vline(x=90, line_width=2, line_dash="dash", line_color="red", annotation_text="Límite 90 días")
    st.plotly_chart(fig_prod_recency, use_container_width=True)

    # 2. Customer Recency
    st.subheader("2. Análisis de Clientes por Producto")
    unique_products = sorted(df['producto'].unique())
    selected_prod = st.selectbox("Selecciona un Producto:", unique_products)

    if selected_prod:
        prod_df = df[df['producto'] == selected_prod]
        
        if not prod_df.empty:
            cust_stats = prod_df.groupby('cliente_nombre').agg({
                'venta_neta': 'sum',
                'fecha': 'max',
                'cantidad': 'sum'
            }).reset_index()
            
            cust_stats['dias_sin_compra'] = (max_recency_date - cust_stats['fecha']).dt.days
            cust_stats['estado'] = cust_stats['dias_sin_compra'].apply(lambda x: 'Inactivo (>90 días)' if x > 90 else 'Activo')
            
            fig_cust_recency = px.scatter(
                cust_stats, 
                x='dias_sin_compra', 
                y='venta_neta',
                size='cantidad',
                color='estado',
                hover_name='cliente_nombre',
                title=f"Clientes de '{selected_prod}'",
                color_discrete_map={'Inactivo (>90 días)': '#ef553b', 'Activo': '#00cc96'},
                template='plotly_dark'
            )
            fig_cust_recency.add_vline(x=90, line_width=2, line_dash="dash", line_color="red")
            st.plotly_chart(fig_cust_recency, use_container_width=True)
            
            risk_cust = cust_stats[cust_stats['dias_sin_compra'] > 90].sort_values('venta_neta', ascending=False)
            if not risk_cust.empty:
                st.warning(f"⚠️ {len(risk_cust)} clientes en riesgo (>90 días).")
                with st.expander("Ver detalle"):
                    st.dataframe(risk_cust[['cliente_nombre', 'dias_sin_compra', 'venta_neta']])


def render_customer_deep_dive():
    st.title("🔎 Explorador de Clientes")
    st.caption("Investigación profunda del historial de compras por cliente.")
    
    max_recency_date = df['fecha'].max()
    
    # Global Customer Recency Chart
    st.subheader("📊 Estado de Clientes (Global)")
    st.caption("Muestra solo clientes con más de 7 transacciones o compras superiores a $10,000")
    
    cust_global = df.groupby('cliente_nombre').agg({
        'venta_neta': 'sum',
        'fecha': ['max', 'count']
    }).reset_index()
    cust_global.columns = ['cliente', 'venta_neta', 'fecha', 'transacciones']
    
    # Filter: >7 transactions OR >$10,000 in sales
    cust_global = cust_global[(cust_global['transacciones'] > 7) | (cust_global['venta_neta'] > 10000)]
    
    cust_global['dias_sin_compra'] = (max_recency_date - cust_global['fecha']).dt.days
    cust_global['estado'] = cust_global['dias_sin_compra'].apply(
        lambda x: 'Alerta (>90 días)' if x > 90 else 'Activo'
    )
    
    fig_cust_global = px.scatter(
        cust_global,
        x='dias_sin_compra',
        y='venta_neta',
        color='estado',
        hover_name='cliente',
        hover_data={'transacciones': True},
        title=f'Clientes Relevantes: Ventas vs Días sin Comprar ({len(cust_global)} clientes)',
        color_discrete_map={'Alerta (>90 días)': '#ef553b', 'Activo': '#00cc96'},
        template='plotly_dark'
    )
    fig_cust_global.add_vline(x=90, line_width=2, line_dash="dash", line_color="red", annotation_text="Límite 90 días")
    st.plotly_chart(fig_cust_global, use_container_width=True)
    
    st.markdown("---")
    
    # Individual Customer Lookup
    st.subheader("🔍 Búsqueda de Cliente Individual")
    unique_customers = sorted(df['cliente_nombre'].unique())
    selected_customer = st.selectbox("Buscar Cliente:", unique_customers)

    if selected_customer:
        cust_df = df[df['cliente_nombre'] == selected_customer]
        
        if not cust_df.empty:
            col_metrics1, col_metrics2, col_metrics3 = st.columns(3)
            col_metrics1.metric("Total Comprado", f"${cust_df['venta_neta'].sum():,.2f}")
            col_metrics2.metric("Artículos Totales", f"{cust_df['cantidad'].sum():,.0f}")
            col_metrics3.metric("Última Compra", cust_df['fecha'].max().strftime('%d/%m/%Y'))
            
            st.subheader("Portafolio de Productos")
            cust_prods = cust_df.groupby('producto').agg({
                'cantidad': 'sum',
                'venta_neta': 'sum',
                'fecha': 'max'
            }).reset_index()
            
            cust_prods['dias_sin_compra'] = (max_recency_date - cust_prods['fecha']).dt.days
            cust_prods['estado'] = cust_prods['dias_sin_compra'].apply(lambda x: 'Alerta (>90 días)' if x > 90 else 'Activo')
            
            fig_cust_prods = px.bar(
                cust_prods,
                x='cantidad',
                y='producto',
                orientation='h',
                color='estado',
                title="Historial de Productos (Color indica actividad reciente)",
                color_discrete_map={'Alerta (>90 días)': '#ef553b', 'Activo': '#00cc96'},
                template='plotly_dark'
            )
            fig_cust_prods.update_layout(yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig_cust_prods, use_container_width=True)


def render_category_analysis():
    st.title("📦 Análisis por Categoría")
    
    if 'categoria' not in filtered_df.columns:
        st.warning("No hay datos de categoría disponibles.")
        return
    
    # Category overview metrics
    cat_stats = filtered_df.groupby('categoria').agg({
        'venta_neta': 'sum',
        'cantidad': 'sum',
        'factura_id': 'nunique',
        'cliente_nombre': 'nunique',
        'producto': 'nunique'
    }).reset_index()
    cat_stats.columns = ['Categoría', 'Ventas', 'Cantidad', 'Transacciones', 'Clientes', 'Productos']
    cat_stats = cat_stats.sort_values('Ventas', ascending=False)
    
    # Top KPIs
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Categorías", len(cat_stats))
    with col2:
        st.metric("Categoría Líder", cat_stats.iloc[0]['Categoría'][:20] + "..." if len(cat_stats.iloc[0]['Categoría']) > 20 else cat_stats.iloc[0]['Categoría'])
    with col3:
        st.metric("Ventas Top Categoría", f"${cat_stats.iloc[0]['Ventas']:,.0f}")
    
    st.markdown("---")
    
    # Two columns layout
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("🏆 Top 15 Categorías por Ventas")
        top_cats = cat_stats.head(15)
        fig_cats = px.bar(
            top_cats,
            x='Ventas',
            y='Categoría',
            orientation='h',
            text='Ventas',
            template='plotly_dark',
            color='Ventas',
            color_continuous_scale='Blues'
        )
        fig_cats.update_traces(texttemplate='$%{text:,.0f}', textposition='outside')
        fig_cats.update_layout(yaxis={'categoryorder': 'total ascending'}, showlegend=False)
        st.plotly_chart(fig_cats, use_container_width=True)
    
    with col_right:
        st.subheader("🥧 Distribución de Ventas")
        top_10 = cat_stats.head(10)
        fig_pie = px.pie(
            top_10,
            values='Ventas',
            names='Categoría',
            template='plotly_dark',
            hole=0.4
        )
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True)
    
    st.markdown("---")
    
    # Category Deep Dive
    st.subheader("🔍 Análisis Detallado por Categoría")
    
    # Category selector
    selected_cat = st.selectbox(
        "Selecciona una categoría:",
        options=cat_stats['Categoría'].tolist()
    )
    
    if selected_cat:
        cat_df = filtered_df[filtered_df['categoria'] == selected_cat]
        
        # Category metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Ventas Totales", f"${cat_df['venta_neta'].sum():,.0f}")
        with col2:
            st.metric("Cantidad Vendida", f"{cat_df['cantidad'].sum():,.0f}")
        with col3:
            st.metric("Clientes Únicos", cat_df['cliente_nombre'].nunique())
        with col4:
            st.metric("Productos", cat_df['producto'].nunique())
        
        st.markdown("---")
        
        # Two tabs for different analyses
        tab1, tab2, tab3 = st.tabs(["👥 Clientes", "📦 Productos", "📈 Tendencia"])
        
        with tab1:
            st.subheader(f"Clientes que Compran {selected_cat[:30]}")
            
            # Customer breakdown for this category
            cust_cat = cat_df.groupby('cliente_nombre').agg({
                'venta_neta': 'sum',
                'cantidad': 'sum',
                'fecha': ['min', 'max', 'count']
            }).reset_index()
            cust_cat.columns = ['Cliente', 'Ventas', 'Cantidad', 'Primera Compra', 'Última Compra', 'Transacciones']
            cust_cat = cust_cat.sort_values('Ventas', ascending=False)
            
            # Days since last purchase
            today = filtered_df['fecha'].max()
            cust_cat['Días Sin Comprar'] = (today - cust_cat['Última Compra']).dt.days
            cust_cat['Estado'] = cust_cat['Días Sin Comprar'].apply(
                lambda x: '🔴 Inactivo' if x > 90 else ('🟡 En Riesgo' if x > 30 else '🟢 Activo')
            )
            
            # Top customers chart
            top_custs = cust_cat.head(15)
            fig_custs = px.bar(
                top_custs,
                x='Ventas',
                y='Cliente',
                orientation='h',
                color='Ventas',
                template='plotly_dark',
                color_continuous_scale='Greens'
            )
            fig_custs.update_layout(yaxis={'categoryorder': 'total ascending'}, showlegend=False)
            st.plotly_chart(fig_custs, use_container_width=True)
            
            # Customer table
            st.dataframe(
                cust_cat[['Cliente', 'Ventas', 'Cantidad', 'Transacciones', 'Días Sin Comprar', 'Estado']].head(20),
                hide_index=True,
                use_container_width=True
            )
        
        with tab2:
            st.subheader(f"Productos en {selected_cat[:30]}")
            
            # Product breakdown
            prod_cat = cat_df.groupby('producto').agg({
                'venta_neta': 'sum',
                'cantidad': 'sum',
                'cliente_nombre': 'nunique',
                'fecha': 'max'
            }).reset_index()
            prod_cat.columns = ['Producto', 'Ventas', 'Cantidad', 'Clientes', 'Última Venta']
            prod_cat = prod_cat.sort_values('Ventas', ascending=False)
            
            # Products chart
            top_prods = prod_cat.head(15)
            fig_prods = px.bar(
                top_prods,
                x='Ventas',
                y='Producto',
                orientation='h',
                color='Ventas',
                template='plotly_dark',
                color_continuous_scale='Oranges'
            )
            fig_prods.update_layout(yaxis={'categoryorder': 'total ascending'}, showlegend=False)
            st.plotly_chart(fig_prods, use_container_width=True)
            
            # Product table
            st.dataframe(
                prod_cat.head(20),
                hide_index=True,
                use_container_width=True
            )
        
        with tab3:
            st.subheader(f"Tendencia Mensual - {selected_cat[:30]}")
            
            # Create month column for grouping
            cat_df_trend = cat_df.copy()
            cat_df_trend['mes_año'] = cat_df_trend['fecha'].dt.to_period('M').astype(str)
            
            # Monthly trend for category
            cat_trend = cat_df_trend.groupby('mes_año')['venta_neta'].sum().reset_index()
            cat_trend = cat_trend.sort_values('mes_año')
            
            fig_trend = px.line(
                cat_trend,
                x='mes_año',
                y='venta_neta',
                markers=True,
                template='plotly_dark',
                labels={'mes_año': 'Mes', 'venta_neta': 'Ventas ($)'}
            )
            fig_trend.update_traces(line_color='#00d4aa', marker_size=8)
            st.plotly_chart(fig_trend, use_container_width=True)
    
    st.markdown("---")
    st.subheader("📊 Tabla Completa de Categorías")
    st.dataframe(cat_stats, hide_index=True, use_container_width=True)


def get_base_category(cat):
    """Extract base category name by removing numeric suffix."""
    import re
    if not isinstance(cat, str):
        return 'OTROS'
    # Remove numbers and dashes at the end, keep the base name
    # Examples: TELA AUTO-1000 -> TELA AUTO, PVC BONDE -3116 -> PVC BONDE
    base = re.sub(r'[\s-]*[\d]+$', '', cat).strip()
    base = re.sub(r'[\s-]+$', '', base).strip()
    return base if base else cat


def render_grouped_category_analysis():
    st.title("📦 Categorías Agrupadas")
    st.caption("Análisis con categorías combinadas (ej: TELA AUTO-1000 y TELA AUTO-500 = TELA AUTO)")
    
    if 'categoria' not in filtered_df.columns:
        st.warning("No hay datos de categoría disponibles.")
        return
    
    # Create grouped category column
    df_grouped = filtered_df.copy()
    df_grouped['categoria_base'] = df_grouped['categoria'].apply(get_base_category)
    
    # Category overview metrics
    cat_stats = df_grouped.groupby('categoria_base').agg({
        'venta_neta': 'sum',
        'cantidad': 'sum',
        'factura_id': 'nunique',
        'cliente_nombre': 'nunique',
        'producto': 'nunique'
    }).reset_index()
    cat_stats.columns = ['Categoría', 'Ventas', 'Cantidad', 'Transacciones', 'Clientes', 'Productos']
    cat_stats = cat_stats.sort_values('Ventas', ascending=False)
    
    # Top KPIs
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Grupos", len(cat_stats))
    with col2:
        st.metric("Grupo Líder", cat_stats.iloc[0]['Categoría'][:20] + "..." if len(cat_stats.iloc[0]['Categoría']) > 20 else cat_stats.iloc[0]['Categoría'])
    with col3:
        st.metric("Ventas Top Grupo", f"${cat_stats.iloc[0]['Ventas']:,.0f}")
    
    st.markdown("---")
    
    # Two columns layout
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("🏆 Top 15 Grupos por Ventas")
        top_cats = cat_stats.head(15)
        fig_cats = px.bar(
            top_cats,
            x='Ventas',
            y='Categoría',
            orientation='h',
            text='Ventas',
            template='plotly_dark',
            color='Ventas',
            color_continuous_scale='Viridis'
        )
        fig_cats.update_traces(texttemplate='$%{text:,.0f}', textposition='outside')
        fig_cats.update_layout(yaxis={'categoryorder': 'total ascending'}, showlegend=False)
        st.plotly_chart(fig_cats, use_container_width=True)
    
    with col_right:
        st.subheader("🥧 Distribución de Ventas")
        top_10 = cat_stats.head(10)
        fig_pie = px.pie(
            top_10,
            values='Ventas',
            names='Categoría',
            template='plotly_dark',
            hole=0.4
        )
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True)
    
    st.markdown("---")
    
    # Group Deep Dive
    st.subheader("🔍 Análisis Detallado por Grupo")
    
    # Group selector
    selected_group = st.selectbox(
        "Selecciona un grupo:",
        options=cat_stats['Categoría'].tolist(),
        key="grouped_cat_select"
    )
    
    if selected_group:
        group_df = df_grouped[df_grouped['categoria_base'] == selected_group]
        
        # Show which original categories are included
        original_cats = group_df['categoria'].unique()
        with st.expander(f"📋 Incluye {len(original_cats)} categorías originales"):
            st.write(", ".join(sorted(original_cats)[:20]))
            if len(original_cats) > 20:
                st.caption(f"... y {len(original_cats) - 20} más")
        
        # Group metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Ventas Totales", f"${group_df['venta_neta'].sum():,.0f}")
        with col2:
            st.metric("Cantidad Vendida", f"{group_df['cantidad'].sum():,.0f}")
        with col3:
            st.metric("Clientes Únicos", group_df['cliente_nombre'].nunique())
        with col4:
            st.metric("Productos", group_df['producto'].nunique())
        
        st.markdown("---")
        
        # Tabs for different analyses
        tab1, tab2, tab3 = st.tabs(["👥 Clientes", "📦 Productos", "📈 Tendencia"])
        
        with tab1:
            st.subheader(f"Clientes que Compran {selected_group[:30]}")
            
            cust_grp = group_df.groupby('cliente_nombre').agg({
                'venta_neta': 'sum',
                'cantidad': 'sum',
                'fecha': ['min', 'max', 'count']
            }).reset_index()
            cust_grp.columns = ['Cliente', 'Ventas', 'Cantidad', 'Primera Compra', 'Última Compra', 'Transacciones']
            cust_grp = cust_grp.sort_values('Ventas', ascending=False)
            
            today = filtered_df['fecha'].max()
            cust_grp['Días Sin Comprar'] = (today - cust_grp['Última Compra']).dt.days
            cust_grp['Estado'] = cust_grp['Días Sin Comprar'].apply(
                lambda x: '🔴 Inactivo' if x > 90 else ('🟡 En Riesgo' if x > 30 else '🟢 Activo')
            )
            
            top_custs = cust_grp.head(15)
            fig_custs = px.bar(
                top_custs,
                x='Ventas',
                y='Cliente',
                orientation='h',
                color='Ventas',
                template='plotly_dark',
                color_continuous_scale='Greens'
            )
            fig_custs.update_layout(yaxis={'categoryorder': 'total ascending'}, showlegend=False)
            st.plotly_chart(fig_custs, use_container_width=True)
            
            st.dataframe(
                cust_grp[['Cliente', 'Ventas', 'Cantidad', 'Transacciones', 'Días Sin Comprar', 'Estado']].head(20),
                hide_index=True,
                use_container_width=True
            )
        
        with tab2:
            st.subheader(f"Productos en {selected_group[:30]}")
            
            prod_grp = group_df.groupby('producto').agg({
                'venta_neta': 'sum',
                'cantidad': 'sum',
                'cliente_nombre': 'nunique',
                'fecha': 'max'
            }).reset_index()
            prod_grp.columns = ['Producto', 'Ventas', 'Cantidad', 'Clientes', 'Última Venta']
            prod_grp = prod_grp.sort_values('Ventas', ascending=False)
            
            top_prods = prod_grp.head(15)
            fig_prods = px.bar(
                top_prods,
                x='Ventas',
                y='Producto',
                orientation='h',
                color='Ventas',
                template='plotly_dark',
                color_continuous_scale='Oranges'
            )
            fig_prods.update_layout(yaxis={'categoryorder': 'total ascending'}, showlegend=False)
            st.plotly_chart(fig_prods, use_container_width=True)
            
            st.dataframe(prod_grp.head(20), hide_index=True, use_container_width=True)
        
        with tab3:
            st.subheader(f"Tendencia Mensual - {selected_group[:30]}")
            
            group_df_trend = group_df.copy()
            group_df_trend['mes_año'] = group_df_trend['fecha'].dt.to_period('M').astype(str)
            
            grp_trend = group_df_trend.groupby('mes_año')['venta_neta'].sum().reset_index()
            grp_trend = grp_trend.sort_values('mes_año')
            
            fig_trend = px.line(
                grp_trend,
                x='mes_año',
                y='venta_neta',
                markers=True,
                template='plotly_dark',
                labels={'mes_año': 'Mes', 'venta_neta': 'Ventas ($)'}
            )
            fig_trend.update_traces(line_color='#00d4aa', marker_size=8)
            st.plotly_chart(fig_trend, use_container_width=True)
    
    st.markdown("---")
    st.subheader("📊 Tabla Completa de Grupos")
    st.dataframe(cat_stats, hide_index=True, use_container_width=True)


def render_reminders():
    st.title("📢 Recordatorios de Negocio")
    st.caption("Insights valiosos para la toma de decisiones. API disponible en puerto 8502.")
    
    today = df['fecha'].max()
    current_month = today.month
    current_year = today.year
    
    # --- 1. SALES TARGET ---
    st.subheader("🎯 Meta de Ventas del Mes")
    
    # Get sales for current month across all years
    df_month = df[df['fecha'].dt.month == current_month].copy()
    yearly_sales = df_month.groupby(df_month['fecha'].dt.year).agg({
        'venta_neta': 'sum'
    }).reset_index()
    yearly_sales.columns = ['año', 'ventas']
    yearly_sales = yearly_sales.sort_values('año', ascending=False)
    
    historical = yearly_sales[yearly_sales['año'] < current_year]
    current = yearly_sales[yearly_sales['año'] == current_year]
    
    avg_sales = historical['ventas'].mean() if not historical.empty else 0
    max_sales = historical['ventas'].max() if not historical.empty else 0
    current_sales = current['ventas'].sum() if not current.empty else 0
    
    days_in_month = 31  # Simplified
    days_elapsed = today.day
    projected = (current_sales / days_elapsed * days_in_month) if days_elapsed > 0 else 0
    meta = avg_sales * 1.1  # 10% above average
    pct = (current_sales / meta * 100) if meta > 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Ventas Actuales", f"${current_sales:,.0f}")
    col2.metric("Meta Sugerida", f"${meta:,.0f}")
    col3.metric("Promedio Histórico", f"${avg_sales:,.0f}")
    col4.metric("% de Meta", f"{pct:.1f}%", delta=f"{pct-100:.1f}%" if pct != 0 else None)
    
    # Progress bar
    progress = min(pct / 100, 1.0)
    st.progress(progress, text=f"Progreso hacia la meta: {pct:.1f}%")
    
    # Historical comparison chart
    if not yearly_sales.empty:
        fig_hist = px.bar(
            yearly_sales,
            x='año',
            y='ventas',
            title=f'Ventas del Mes {today.strftime("%B")} por Año',
            template='plotly_dark',
            color='ventas',
            color_continuous_scale='Blues'
        )
        fig_hist.add_hline(y=meta, line_dash="dash", line_color="green", annotation_text="Meta")
        st.plotly_chart(fig_hist, use_container_width=True)
    
    st.markdown("---")
    
    # --- 2. INACTIVE CUSTOMERS ---
    st.subheader("👥 Clientes Inactivos (>90 días)")
    
    cust_stats = df.groupby('cliente_nombre').agg({
        'venta_neta': 'sum',
        'fecha': ['max', 'count']
    }).reset_index()
    cust_stats.columns = ['cliente', 'total_ventas', 'ultima_compra', 'transacciones']
    cust_stats['dias_sin_compra'] = (today - cust_stats['ultima_compra']).dt.days
    
    # Filter relevant (>3 transactions OR >$5000)
    relevant = cust_stats[(cust_stats['transacciones'] > 3) | (cust_stats['total_ventas'] > 5000)]
    inactive = relevant[relevant['dias_sin_compra'] > 90].sort_values('total_ventas', ascending=False)
    
    col1, col2 = st.columns(2)
    col1.metric("Clientes en Riesgo", len(inactive))
    col2.metric("Valor en Riesgo", f"${inactive['total_ventas'].sum():,.0f}")
    
    if not inactive.empty:
        st.warning(f"⚠️ {len(inactive)} clientes importantes sin comprar en más de 90 días")
        
        inactive_display = inactive[['cliente', 'total_ventas', 'transacciones', 'dias_sin_compra', 'ultima_compra']].head(15).copy()
        inactive_display['ultima_compra'] = inactive_display['ultima_compra'].dt.strftime('%d/%m/%Y')
        inactive_display.columns = ['Cliente', 'Ventas Totales', 'Transacciones', 'Días Inactivo', 'Última Compra']
        st.dataframe(inactive_display, hide_index=True, use_container_width=True)
    else:
        st.success("✅ No hay clientes importantes inactivos")
    
    st.markdown("---")
    
    # --- 3. STALE TOP PRODUCTS ---
    st.subheader("📦 Productos Top Sin Movimiento (>60 días)")
    
    prod_stats = df.groupby('producto').agg({
        'venta_neta': 'sum',
        'fecha': ['max', 'count']
    }).reset_index()
    prod_stats.columns = ['producto', 'total_ventas', 'ultima_venta', 'transacciones']
    prod_stats['dias_sin_venta'] = (today - prod_stats['ultima_venta']).dt.days
    
    # Top 50 products by sales
    top_products = prod_stats.nlargest(50, 'total_ventas')
    stale = top_products[top_products['dias_sin_venta'] > 60].sort_values('total_ventas', ascending=False)
    
    col1, col2 = st.columns(2)
    col1.metric("Productos Afectados", len(stale))
    col2.metric("Ventas Históricas", f"${stale['total_ventas'].sum():,.0f}")
    
    if not stale.empty:
        st.warning(f"⚠️ {len(stale)} productos populares sin ventas en más de 60 días")
        
        stale_display = stale[['producto', 'total_ventas', 'transacciones', 'dias_sin_venta', 'ultima_venta']].head(15).copy()
        stale_display['ultima_venta'] = stale_display['ultima_venta'].dt.strftime('%d/%m/%Y')
        stale_display.columns = ['Producto', 'Ventas Totales', 'Transacciones', 'Días Sin Venta', 'Última Venta']
        st.dataframe(stale_display, hide_index=True, use_container_width=True)
    else:
        st.success("✅ Todos los productos top están activos")
    
    st.markdown("---")
    
    # --- 4. COMPARACIÓN MENSUAL DE CLIENTES (3 MESES) ---
    st.subheader("📊 Top Clientes - Comparación 3 Meses")
    
    def get_month_num(current, offset):
        m = current - offset
        if m <= 0:
            m += 12
        return m
    
    mes_actual = current_month
    mes_anterior = get_month_num(current_month, 1)
    mes_anterior_2 = get_month_num(current_month, 2)
    
    st.caption(f"Meses comparados: {mes_actual} (actual) vs {mes_anterior} (anterior) vs {mes_anterior_2} (hace 2 meses)")
    
    df_mes_actual = df[df['fecha'].dt.month == mes_actual]
    df_mes_ant1 = df[df['fecha'].dt.month == mes_anterior]
    df_mes_ant2 = df[df['fecha'].dt.month == mes_anterior_2]
    
    clientes_m0 = df_mes_actual.groupby('cliente_nombre')['venta_neta'].sum().nlargest(20).reset_index()
    clientes_m0.columns = ['Cliente', 'Mes Actual']
    clientes_m1 = df_mes_ant1.groupby('cliente_nombre')['venta_neta'].sum().reset_index()
    clientes_m1.columns = ['Cliente', 'Mes Anterior']
    clientes_m2 = df_mes_ant2.groupby('cliente_nombre')['venta_neta'].sum().reset_index()
    clientes_m2.columns = ['Cliente', 'Hace 2 Meses']
    
    comp_clientes = clientes_m0.merge(clientes_m1, on='Cliente', how='left').merge(clientes_m2, on='Cliente', how='left').fillna(0)
    comp_clientes['Cambio vs Anterior'] = comp_clientes['Mes Actual'] - comp_clientes['Mes Anterior']
    comp_clientes['Cambio vs Hace 2'] = comp_clientes['Mes Actual'] - comp_clientes['Hace 2 Meses']
    
    st.dataframe(comp_clientes.round(2), hide_index=True, use_container_width=True)
    
    st.markdown("---")
    
    # --- 5. COMPARACIÓN MENSUAL DE PRODUCTOS (3 MESES) ---
    st.subheader("📦 Top Productos - Comparación 3 Meses")
    
    prods_m0 = df_mes_actual.groupby('producto')['venta_neta'].sum().nlargest(20).reset_index()
    prods_m0.columns = ['Producto', 'Mes Actual']
    prods_m1 = df_mes_ant1.groupby('producto')['venta_neta'].sum().reset_index()
    prods_m1.columns = ['Producto', 'Mes Anterior']
    prods_m2 = df_mes_ant2.groupby('producto')['venta_neta'].sum().reset_index()
    prods_m2.columns = ['Producto', 'Hace 2 Meses']
    
    comp_productos = prods_m0.merge(prods_m1, on='Producto', how='left').merge(prods_m2, on='Producto', how='left').fillna(0)
    comp_productos['Cambio vs Anterior'] = comp_productos['Mes Actual'] - comp_productos['Mes Anterior']
    comp_productos['Cambio vs Hace 2'] = comp_productos['Mes Actual'] - comp_productos['Hace 2 Meses']
    
    st.dataframe(comp_productos.round(2), hide_index=True, use_container_width=True)
    
    st.markdown("---")
    
    # --- API INFO ---
    st.subheader("🔗 API para Asistentes")
    st.info("""
    **Endpoints disponibles en http://localhost:8502:**
    
    - `POST /api/push-to-n8n` - Enviar todos los datos a n8n
    - `GET /api/reminders` - Obtener todos los recordatorios
    
    **Para enviar a n8n:**
    ```bash
    curl -X POST http://localhost:8502/api/push-to-n8n
    ```
    """)



def render_config():
    st.title("⚙️ Configuración y Carga de Datos")
    
    st.markdown("### 📥 Actualizar Datos")
    st.info(f"Ruta actual del archivo: `{DATA_PATH}`")
    
    uploaded_file = st.file_uploader("Subir nuevo archivo de ventas (CSV)", type=['csv'])
    
    if uploaded_file is not None:
        if st.button("Confirmar y Actualizar"):
            try:
                # Save file
                with open(DATA_PATH, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # Clear cache
                st.cache_data.clear()
                
                st.success("✅ Archivo actualizado correctamente. La caché ha sido limpiada.")
                st.rerun()
            except Exception as e:
                st.error(f"Error al guardar el archivo: {e}")

    st.markdown("---")
    st.markdown("### 🗑️ Mantenimiento")
    if st.button("Limpiar Caché Manualmente"):
        st.cache_data.clear()
        st.success("Caché limpiada.")
        st.rerun()


def render_raw_data():
    st.title("📄 Datos Crudos")
    st.dataframe(filtered_df.sort_values(by='fecha', ascending=False))


# --- MAIN ROUTING ---

if selected_view == "Visión General":
    render_overview()
elif selected_view == "📢 Recordatorios":
    render_reminders()
elif selected_view == "Análisis por Categoría":
    render_category_analysis()
elif selected_view == "Categorías Agrupadas":
    render_grouped_category_analysis()
elif selected_view == "Análisis de Recencia":
    render_recency_analysis()
elif selected_view == "Explorador de Clientes":
    render_customer_deep_dive()
elif selected_view == "Datos Crudos":
    render_raw_data()
elif selected_view == "⚙️ Configuración":
    render_config()
