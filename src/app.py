
import streamlit as st
import pandas as pd
import plotly.express as px
from data_loader import load_data, get_kpis, normalize_products
import io

# --- HELPER FUNCTIONS FOR UI ENHANCEMENTS ---

def styled_metric(label, value, delta=None, delta_color="normal"):
    """Display a metric with colored delta and arrow."""
    if delta is not None:
        if delta > 0:
            arrow = "↑"
            color = "#00cc96"  # Green
            delta_text = f"+{delta:.1f}%"
        elif delta < 0:
            arrow = "↓"
            color = "#ef553b"  # Red
            delta_text = f"{delta:.1f}%"
        else:
            arrow = "→"
            color = "#ffa500"  # Orange
            delta_text = "0%"
        
        if delta_color == "inverse":  # For metrics where lower is better
            color = "#ef553b" if delta > 0 else "#00cc96"
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1e1e2e 0%, #2d2d44 100%); 
                    padding: 1rem; border-radius: 10px; border-left: 4px solid {color};">
            <p style="margin: 0; color: #888; font-size: 0.85rem;">{label}</p>
            <p style="margin: 0; font-size: 1.5rem; font-weight: bold; color: white;">{value}</p>
            <p style="margin: 0; color: {color}; font-size: 0.9rem;">{arrow} {delta_text}</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.metric(label, value)


def export_dataframe(df, filename, key):
    """Add export buttons for CSV and Excel."""
    col1, col2 = st.columns([1, 1])
    
    # CSV export
    csv = df.to_csv(index=False).encode('utf-8')
    col1.download_button(
        label="📥 Exportar CSV",
        data=csv,
        file_name=f"{filename}.csv",
        mime="text/csv",
        key=f"csv_{key}"
    )
    
    # Excel export
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Datos')
    excel_data = buffer.getvalue()
    col2.download_button(
        label="📥 Exportar Excel",
        data=excel_data,
        file_name=f"{filename}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key=f"excel_{key}"
    )


def show_model_explanation(model_name, description, metrics_dict, tips=None):
    """Display model explanation with metrics."""
    with st.expander(f"ℹ️ Cómo funciona: {model_name}", expanded=False):
        st.markdown(f"**{model_name}**")
        st.markdown(description)
        
        if metrics_dict:
            st.markdown("**Métricas del modelo:**")
            cols = st.columns(len(metrics_dict))
            for i, (metric_name, metric_value) in enumerate(metrics_dict.items()):
                cols[i].metric(metric_name, metric_value)
        
        if tips:
            st.info(f"💡 **Tip:** {tips}")


def show_confidence_interval(prediction, std_dev, confidence=0.95):
    """Calculate and display confidence interval."""
    import scipy.stats as stats
    z = stats.norm.ppf((1 + confidence) / 2)
    lower = prediction - z * std_dev
    upper = prediction + z * std_dev
    return lower, upper

# Page Configuration
st.set_page_config(
    page_title="Dashboard de Ventas",
    page_icon="bar_chart",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- PASSWORD PROTECTION ---
DASHBOARD_PIN = "101010"
MAX_ATTEMPTS = 5
LOCKOUT_MINUTES = 5

def check_password():
    """Returns True if the user has entered the correct password."""
    from datetime import datetime, timedelta
    
    # Initialize attempt counter and lockout time if not exists
    if "failed_attempts" not in st.session_state:
        st.session_state["failed_attempts"] = 0
    if "lockout_until" not in st.session_state:
        st.session_state["lockout_until"] = None
    
    # Check if currently locked out
    if st.session_state["lockout_until"]:
        if datetime.now() < st.session_state["lockout_until"]:
            remaining = (st.session_state["lockout_until"] - datetime.now()).seconds // 60 + 1
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
                color: #ef553b;
            }
            </style>
            """, unsafe_allow_html=True)
            
            st.markdown("<div class='login-container'>", unsafe_allow_html=True)
            st.markdown("<p class='login-title'>🔒 Acceso Bloqueado</p>", unsafe_allow_html=True)
            st.error(f"⛔ Demasiados intentos fallidos. Espera {remaining} minuto(s) para intentar de nuevo.")
            st.markdown("</div>", unsafe_allow_html=True)
            return False
        else:
            # Lockout expired, reset
            st.session_state["failed_attempts"] = 0
            st.session_state["lockout_until"] = None
    
    def password_entered():
        """Checks whether the password is correct."""
        if st.session_state.get("password") == DASHBOARD_PIN:
            st.session_state["password_correct"] = True
            st.session_state["failed_attempts"] = 0  # Reset on success
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False
            st.session_state["failed_attempts"] += 1
            # Lock out after MAX_ATTEMPTS
            if st.session_state["failed_attempts"] >= MAX_ATTEMPTS:
                st.session_state["lockout_until"] = datetime.now() + timedelta(minutes=LOCKOUT_MINUTES)
            if "password" in st.session_state:
                del st.session_state["password"]
    
    # Login form styles
    login_styles = """
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
    """
    
    # First run or not authenticated
    if "password_correct" not in st.session_state:
        st.markdown(login_styles, unsafe_allow_html=True)
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
        st.markdown(login_styles, unsafe_allow_html=True)
        st.markdown("<div class='login-container'>", unsafe_allow_html=True)
        st.markdown("<p class='login-title'>🔐 Dashboard de Ventas</p>", unsafe_allow_html=True)
        st.text_input(
            "Ingresa el PIN de acceso:",
            type="password",
            on_change=password_entered,
            key="password",
            placeholder="••••••"
        )
        attempts_left = MAX_ATTEMPTS - st.session_state["failed_attempts"]
        if attempts_left > 0:
            st.error(f"❌ PIN incorrecto. Te quedan {attempts_left} intento(s).")
        st.markdown("</div>", unsafe_allow_html=True)
        return False
    
    # Password correct
    return True

# Check password before showing anything
if not check_password():
    st.stop()

# Custom CSS for Dark/Premium Look + Mobile Responsiveness
st.markdown("""
    <style>
    /* === BASE STYLES === */
    .main {
        background-color: #0e1117;
    }
    .stMetric {
        background-color: #262730;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #3d3f4b;
    }
    
    /* === MOBILE RESPONSIVE STYLES === */
    @media (max-width: 768px) {
        /* Make sidebar collapsible and smaller */
        [data-testid="stSidebar"] {
            min-width: 0 !important;
        }
        
        [data-testid="stSidebar"][aria-expanded="true"] {
            min-width: 280px !important;
            max-width: 280px !important;
        }
        
        /* Larger touch targets for sidebar items */
        [data-testid="stSidebar"] .stRadio > div {
            gap: 0.5rem !important;
        }
        
        [data-testid="stSidebar"] .stRadio label {
            padding: 0.75rem 1rem !important;
            font-size: 1rem !important;
            min-height: 48px !important;
            display: flex !important;
            align-items: center !important;
        }
        
        /* Main content adjustments */
        .main .block-container {
            padding: 1rem 0.75rem !important;
            max-width: 100% !important;
        }
        
        /* Titles - Larger and centered on mobile */
        .main h1 {
            font-size: 1.5rem !important;
            text-align: center !important;
            padding: 0 0.5rem !important;
        }
        
        .main h2 {
            font-size: 1.25rem !important;
        }
        
        .main h3 {
            font-size: 1.1rem !important;
        }
        
        /* Metrics - Stack vertically and make them bigger */
        [data-testid="stMetric"] {
            padding: 1rem !important;
            margin-bottom: 0.5rem !important;
        }
        
        [data-testid="stMetric"] [data-testid="stMetricValue"] {
            font-size: 1.75rem !important;
            font-weight: 700 !important;
        }
        
        [data-testid="stMetric"] [data-testid="stMetricLabel"] {
            font-size: 0.85rem !important;
        }
        
        /* === CRITICAL: FORCE SINGLE COLUMN LAYOUT === */
        /* This prevents horizontal scroll on mobile */
        
        /* Force all columns to stack vertically */
        [data-testid="column"] {
            width: 100% !important;
            flex: 1 1 100% !important;
            min-width: 100% !important;
            max-width: 100% !important;
        }
        
        /* Force horizontal layouts to wrap */
        .row-widget.stHorizontal,
        [data-testid="stHorizontalBlock"] {
            flex-direction: column !important;
            flex-wrap: wrap !important;
        }
        
        .row-widget.stHorizontal > div,
        [data-testid="stHorizontalBlock"] > div {
            width: 100% !important;
            min-width: 100% !important;
            max-width: 100% !important;
            flex: 1 1 100% !important;
        }
        
        /* Prevent any overflow */
        .main, .block-container, [data-testid="stAppViewContainer"] {
            overflow-x: hidden !important;
            max-width: 100vw !important;
        }
        
        /* Charts must fit screen */
        .stPlotlyChart, .js-plotly-plot, .plot-container {
            width: 100% !important;
            max-width: 100% !important;
        }
        
        .js-plotly-plot .plotly {
            width: 100% !important;
        }
        
        /* Images and media */
        img, video, iframe {
            max-width: 100% !important;
            height: auto !important;
        }
        
        /* Tables - Horizontal scroll with indicator */
        [data-testid="stDataFrame"],
        .stDataFrame {
            overflow-x: auto !important;
            -webkit-overflow-scrolling: touch !important;
        }
        
        [data-testid="stDataFrame"]::after {
            content: "← Desliza para ver más →";
            display: block;
            text-align: center;
            font-size: 0.75rem;
            color: #666;
            padding: 0.5rem;
        }
        
        /* Buttons - Bigger touch targets */
        .stButton > button {
            min-height: 48px !important;
            font-size: 1rem !important;
            padding: 0.5rem 1rem !important;
            width: 100% !important;
        }
        
        .stDownloadButton > button {
            min-height: 44px !important;
            font-size: 0.9rem !important;
            width: 100% !important;
            margin-bottom: 0.5rem !important;
        }
        
        /* Input fields - Larger for easier typing */
        .stTextInput input,
        .stSelectbox select,
        .stNumberInput input {
            min-height: 48px !important;
            font-size: 16px !important; /* Prevents iOS zoom */
            padding: 0.75rem !important;
        }
        
        /* Charts - Full width */
        [data-testid="stPlotlyChart"] {
            width: 100% !important;
        }
        
        .js-plotly-plot {
            width: 100% !important;
        }
        
        /* Expander - Easier to tap */
        .streamlit-expanderHeader {
            min-height: 48px !important;
            font-size: 1rem !important;
            padding: 0.75rem !important;
        }
        
        /* Tabs - Larger touch targets */
        .stTabs [data-baseweb="tab-list"] {
            gap: 0 !important;
        }
        
        .stTabs [data-baseweb="tab"] {
            min-height: 48px !important;
            padding: 0.75rem 1rem !important;
            font-size: 0.9rem !important;
            flex: 1 !important;
            justify-content: center !important;
        }
        
        /* Sliders - Bigger touch area */
        .stSlider [data-testid="stTickBar"] {
            padding: 1rem 0 !important;
        }
        
        .stSlider [data-baseweb="slider"] {
            margin-top: 1rem !important;
        }
        
        /* Radio buttons - Bigger */
        .stRadio > div {
            gap: 0.25rem !important;
        }
        
        .stRadio label {
            padding: 0.6rem 1rem !important;
            font-size: 0.95rem !important;
            min-height: 44px !important;
        }
        
        /* Success/Warning/Error messages - More prominent */
        .stSuccess, .stWarning, .stError, .stInfo {
            padding: 1rem !important;
            font-size: 0.95rem !important;
        }
        
        /* Captions - Slightly larger */
        .stCaption {
            font-size: 0.85rem !important;
        }
        
        /* Dividers */
        hr {
            margin: 1rem 0 !important;
        }
        
        /* Plotly chart legend - Hide on very small screens */
        .legend {
            font-size: 10px !important;
        }
    }
    
    /* === EXTRA SMALL PHONES (iPhone SE, etc.) === */
    @media (max-width: 375px) {
        .main h1 {
            font-size: 1.25rem !important;
        }
        
        [data-testid="stMetric"] [data-testid="stMetricValue"] {
            font-size: 1.5rem !important;
        }
        
        .stTabs [data-baseweb="tab"] {
            padding: 0.5rem 0.75rem !important;
            font-size: 0.8rem !important;
        }
        
        .row-widget.stHorizontal > div {
            min-width: 100% !important;
            flex: 1 1 100% !important;
        }
    }
    
    /* === LANDSCAPE MOBILE === */
    @media (max-width: 768px) and (orientation: landscape) {
        .row-widget.stHorizontal > div {
            min-width: 48% !important;
            flex: 1 1 48% !important;
        }
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

# Mobile-Friendly Navigation - Buttons at Top
# Main title in sidebar (for branding on desktop)
st.sidebar.title("📊 Dashboard de Ventas")

# MAIN NAVIGATION - Horizontal radio buttons at TOP (mobile-friendly)
# Using shorter emoji-first labels for mobile
st.markdown("---")
main_sections_short = ["📊 General", "📢 Alertas", "👥 Clientes", "📦 Productos", "📁 Categ.", "🔮 ML", "⚙️ Config"]
main_sections_full = ["📊 Visión General", "📢 Recordatorios", "👥 Clientes", "📦 Productos", "📁 Categorías", "🔮 Predicciones ML", "⚙️ Configuración"]

selected_short = st.radio("Navegación:", main_sections_short, horizontal=True, label_visibility="collapsed", key="main_nav")
selected_idx = main_sections_short.index(selected_short)
selected_section = main_sections_full[selected_idx]

st.markdown("---")

# Sub-section selectors based on main section
selected_view = selected_section  # Default
client_search = ""
product_search = ""

if selected_section == "👥 Clientes":
    client_options_short = ["🔍 Buscar", "👤 Explor.", "🎯 RFM", "⏰ Inact."]
    client_options_full = ["🔍 Buscador", "👤 Explorador", "🎯 Segmentación RFM", "⏰ Inactivos"]
    
    selected_client = st.radio("Sub-sección:", client_options_short, horizontal=True, label_visibility="collapsed", key="client_sub")
    client_idx = client_options_short.index(selected_client)
    selected_view = f"Clientes_{client_options_full[client_idx]}"
    
    # Search box
    client_search = st.text_input("🔎 Buscar cliente:", placeholder="Ej: Textiles...")

elif selected_section == "📦 Productos":
    product_options_short = ["🏆 Top", "📉 Sin Mov.", "⏳ Recencia"]
    product_options_full = ["🏆 Top Productos", "📉 Sin Movimiento", "⏳ Análisis Recencia"]
    
    selected_prod = st.radio("Sub-sección:", product_options_short, horizontal=True, label_visibility="collapsed", key="prod_sub")
    prod_idx = product_options_short.index(selected_prod)
    selected_view = f"Productos_{product_options_full[prod_idx]}"
    
    # Search box  
    product_search = st.text_input("🔎 Buscar producto:", placeholder="Ej: Tela Popelina...", key="product_search")

elif selected_section == "📁 Categorías":
    cat_options_short = ["📊 Por Categ.", "📦 Agrupadas"]
    cat_options_full = ["📊 Por Categoría", "📦 Agrupadas"]
    
    selected_cat = st.radio("Sub-sección:", cat_options_short, horizontal=True, label_visibility="collapsed", key="cat_sub")
    cat_idx = cat_options_short.index(selected_cat)
    selected_view = f"Categorías_{cat_options_full[cat_idx]}"

elif selected_section == "🔮 Predicciones ML":
    ml_options_short = ["📈 Ventas", "📉 Churn", "🛒 Asoc.", "📦 Demanda", "💰 CLV", "🗓️ Estac.", "⏰ Próx."]
    ml_options_full = ["📈 Ventas Futuras", "📉 Riesgo de Churn", "🛒 Productos Asociados", "📦 Demanda por Producto", "💰 Valor del Cliente", "🗓️ Estacionalidad", "⏰ Próxima Compra"]
    
    selected_ml = st.radio("Sub-sección:", ml_options_short, horizontal=True, label_visibility="collapsed", key="ml_sub")
    ml_idx = ml_options_short.index(selected_ml)
    selected_view = f"ML_{ml_options_full[ml_idx]}"

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
    - `GET /api/rfm-segments` - Obtener segmentación RFM
    
    **Para enviar a n8n:**
    ```bash
    curl -X POST http://localhost:8502/api/push-to-n8n
    ```
    """)


def calculate_rfm_scores(dataframe):
    """Calculate RFM scores for each customer."""
    today = dataframe['fecha'].max()
    
    # Calculate RFM metrics per customer
    rfm = dataframe.groupby('cliente_nombre').agg({
        'fecha': 'max',           # Last purchase date (Recency)
        'factura_id': 'nunique',  # Number of transactions (Frequency)
        'venta_neta': 'sum'       # Total revenue (Monetary)
    }).reset_index()
    
    rfm.columns = ['cliente', 'ultima_compra', 'frecuencia', 'valor_monetario']
    rfm['recencia'] = (today - rfm['ultima_compra']).dt.days
    
    # Assign scores 1-5 using quintiles (5 = best)
    # For recency: lower is better, so we invert
    rfm['R_score'] = pd.qcut(rfm['recencia'], 5, labels=[5, 4, 3, 2, 1], duplicates='drop').astype(int)
    rfm['F_score'] = pd.qcut(rfm['frecuencia'].rank(method='first'), 5, labels=[1, 2, 3, 4, 5], duplicates='drop').astype(int)
    rfm['M_score'] = pd.qcut(rfm['valor_monetario'].rank(method='first'), 5, labels=[1, 2, 3, 4, 5], duplicates='drop').astype(int)
    
    # Combined RFM score
    rfm['RFM_score'] = rfm['R_score'].astype(str) + rfm['F_score'].astype(str) + rfm['M_score'].astype(str)
    rfm['RFM_total'] = rfm['R_score'] + rfm['F_score'] + rfm['M_score']
    
    # Assign segments based on RFM scores
    def assign_segment(row):
        r, f, m = row['R_score'], row['F_score'], row['M_score']
        
        if r >= 4 and f >= 4 and m >= 4:
            return '🏆 VIP'
        elif r >= 4 and f >= 4:
            return '💎 Leal'
        elif r >= 4 and m >= 4:
            return '🌟 Potencial'
        elif r <= 2 and f >= 3 and m >= 3:
            return '⚠️ En Riesgo'
        elif r <= 2 and m >= 3:
            return '💤 Dormidos'
        elif r <= 2:
            return '👋 Perdidos'
        elif r >= 4 and f <= 2:
            return '🆕 Nuevos'
        else:
            return '📊 Regular'
    
    rfm['segmento'] = rfm.apply(assign_segment, axis=1)
    
    return rfm


def render_rfm_segmentation():
    st.title("🎯 Segmentación RFM de Clientes")
    st.caption("Clasifica clientes según Recencia, Frecuencia y Valor Monetario")
    
    # Calculate RFM
    rfm = calculate_rfm_scores(df)
    
    # Explanation
    with st.expander("📖 ¿Qué significa cada segmento? (click para ver ejemplos)", expanded=False):
        st.markdown("""
        ### 🏆 VIP - Los Mejores Clientes
        **Cómo se ve:** Compró hace menos de 30 días, tiene más de 20 transacciones, y ha gastado más de $50,000 en total.
        
        **Ejemplo:** *"Textiles del Valle"* - Última compra hace 5 días, 45 transacciones, $120,000 en compras.
        
        **Acción:** Trato VIP, descuentos exclusivos, prioridad en entregas.
        
        ---
        
        ### 💎 Leal - Compradores Frecuentes
        **Cómo se ve:** Compró recientemente y compra seguido, aunque el monto individual no es el más alto.
        
        **Ejemplo:** *"Confecciones María"* - Última compra hace 15 días, 30 transacciones, $25,000 total.
        
        **Acción:** Programas de fidelización, puntos, ofertas regulares.
        
        ---
        
        ### 🌟 Potencial - Alto Valor Reciente
        **Cómo se ve:** Compró recientemente y gasta mucho, pero aún no es frecuente.
        
        **Ejemplo:** *"Industrias Textiles S.A."* - Última compra hace 10 días, solo 5 transacciones pero $80,000 total.
        
        **Acción:** Cultivar la relación, convertir en cliente frecuente.
        
        ---
        
        ### ⚠️ En Riesgo - ¡Recuperar Urgente!
        **Cómo se ve:** Era un cliente excelente (frecuente + alto valor) pero dejó de comprar hace más de 90 días.
        
        **Ejemplo:** *"Modas Express"* - No compra hace 120 días, tenía 25 transacciones, $60,000 total histórico.
        
        **Acción:** Llamar personalmente, ofrecer incentivo especial, entender qué pasó.
        
        ---
        
        ### 💤 Dormidos - Alto Valor Inactivo
        **Cómo se ve:** Gastó mucho históricamente pero no es tan frecuente, y no ha comprado en mucho tiempo.
        
        **Ejemplo:** *"Decoraciones Hogar"* - No compra hace 150 días, 8 transacciones, $45,000 total.
        
        **Acción:** Campañas de reactivación, recordatorios, ofertas de "te extrañamos".
        
        ---
        
        ### 👋 Perdidos - Casi Inactivos
        **Cómo se ve:** No compran hace mucho tiempo, baja frecuencia, bajo valor.
        
        **Ejemplo:** *"Tienda La Esquina"* - No compra hace 200 días, solo 2 transacciones, $500 total.
        
        **Acción:** Último intento de recuperación o descartar del seguimiento activo.
        
        ---
        
        ### 🆕 Nuevos - Clientes Frescos
        **Cómo se ve:** Compraron recientemente pero tienen pocas transacciones (cliente nuevo).
        
        **Ejemplo:** *"Boutique Nueva"* - Primera compra hace 7 días, 1 transacción, $3,000.
        
        **Acción:** Onboarding, bienvenida, construir relación desde inicio.
        
        ---
        
        ### 📊 Regular - Seguimiento Normal
        **Cómo se ve:** No destaca en ninguna métrica particular, cliente promedio.
        
        **Ejemplo:** *"Almacén Centro"* - Última compra hace 45 días, 8 transacciones, $12,000 total.
        
        **Acción:** Mantener comunicación regular, monitorear cambios.
        """)
    
    st.markdown("---")
    
    # --- KEY METRICS ---
    segment_stats = rfm.groupby('segmento').agg({
        'cliente': 'count',
        'valor_monetario': 'sum',
        'frecuencia': 'mean',
        'recencia': 'mean'
    }).reset_index()
    segment_stats.columns = ['Segmento', 'Clientes', 'Valor Total', 'Freq. Promedio', 'Recencia Promedio']
    segment_stats = segment_stats.sort_values('Valor Total', ascending=False)
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Clientes", len(rfm))
    col2.metric("Clientes VIP", len(rfm[rfm['segmento'] == '🏆 VIP']))
    col3.metric("En Riesgo", len(rfm[rfm['segmento'] == '⚠️ En Riesgo']))
    col4.metric("Valor Total", f"${rfm['valor_monetario'].sum():,.0f}")
    
    st.markdown("---")
    
    # --- VISUALIZATIONS ---
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("📊 Distribución por Segmento")
        
        # Define colors for segments
        segment_colors = {
            '🏆 VIP': '#FFD700',
            '💎 Leal': '#00CED1',
            '🌟 Potencial': '#9370DB',
            '⚠️ En Riesgo': '#FF6B6B',
            '💤 Dormidos': '#708090',
            '👋 Perdidos': '#8B0000',
            '🆕 Nuevos': '#32CD32',
            '📊 Regular': '#4169E1'
        }
        
        fig_pie = px.pie(
            segment_stats,
            values='Clientes',
            names='Segmento',
            title='Clientes por Segmento',
            template='plotly_dark',
            color='Segmento',
            color_discrete_map=segment_colors
        )
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col_right:
        st.subheader("💰 Valor por Segmento")
        
        fig_bar = px.bar(
            segment_stats,
            x='Segmento',
            y='Valor Total',
            color='Segmento',
            title='Valor Monetario por Segmento',
            template='plotly_dark',
            color_discrete_map=segment_colors
        )
        fig_bar.update_layout(showlegend=False)
        st.plotly_chart(fig_bar, use_container_width=True)
    
    st.markdown("---")
    
    # --- SCATTER PLOT ---
    st.subheader("🔍 Mapa de Clientes (Recencia vs Valor)")
    
    fig_scatter = px.scatter(
        rfm,
        x='recencia',
        y='valor_monetario',
        color='segmento',
        size='frecuencia',
        hover_name='cliente',
        hover_data={'recencia': True, 'frecuencia': True, 'valor_monetario': ':.2f'},
        title='Todos los Clientes: Recencia vs Valor Monetario (tamaño = frecuencia)',
        template='plotly_dark',
        color_discrete_map=segment_colors
    )
    fig_scatter.add_vline(x=90, line_dash="dash", line_color="red", annotation_text="90 días")
    fig_scatter.update_layout(
        xaxis_title="Días desde última compra",
        yaxis_title="Valor monetario total ($)"
    )
    st.plotly_chart(fig_scatter, use_container_width=True)
    
    st.markdown("---")
    
    # --- DETAILED TABLE ---
    st.subheader("📋 Detalle por Cliente")
    
    # Segment filter
    selected_segments = st.multiselect(
        "Filtrar por segmento:",
        options=rfm['segmento'].unique(),
        default=rfm['segmento'].unique()
    )
    
    filtered_rfm = rfm[rfm['segmento'].isin(selected_segments)]
    
    # Sort options
    sort_by = st.selectbox(
        "Ordenar por:",
        options=['valor_monetario', 'recencia', 'frecuencia', 'RFM_total'],
        format_func=lambda x: {'valor_monetario': 'Valor ($)', 'recencia': 'Recencia', 'frecuencia': 'Frecuencia', 'RFM_total': 'Score RFM'}[x]
    )
    
    sorted_rfm = filtered_rfm.sort_values(sort_by, ascending=(sort_by == 'recencia'))
    
    # Display table
    display_df = sorted_rfm[['cliente', 'segmento', 'recencia', 'frecuencia', 'valor_monetario', 'R_score', 'F_score', 'M_score', 'RFM_score']].copy()
    display_df.columns = ['Cliente', 'Segmento', 'Días Sin Comprar', 'Transacciones', 'Valor Total', 'R', 'F', 'M', 'Score']
    display_df['Valor Total'] = display_df['Valor Total'].apply(lambda x: f"${x:,.2f}")
    
    st.dataframe(display_df.head(50), hide_index=True, use_container_width=True)
    
    # Summary stats
    st.markdown("---")
    st.subheader("📈 Resumen por Segmento")
    summary_display = segment_stats.copy()
    summary_display['Valor Total'] = summary_display['Valor Total'].apply(lambda x: f"${x:,.0f}")
    summary_display['Freq. Promedio'] = summary_display['Freq. Promedio'].apply(lambda x: f"{x:.1f}")
    summary_display['Recencia Promedio'] = summary_display['Recencia Promedio'].apply(lambda x: f"{x:.0f} días")
    st.dataframe(summary_display, hide_index=True, use_container_width=True)



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


def render_client_search(search_term):
    """Search and display client details based on search term."""
    st.title("🔍 Buscador de Clientes")
    
    if not search_term:
        st.info("👆 Ingresa el nombre de un cliente en la barra lateral para buscarlo.")
        
        # Show all clients as a list
        st.subheader("📋 Lista de Clientes")
        all_clients = df.groupby('cliente_nombre').agg({
            'venta_neta': 'sum',
            'fecha': ['max', 'count']
        }).reset_index()
        all_clients.columns = ['Cliente', 'Ventas Totales', 'Última Compra', 'Transacciones']
        all_clients = all_clients.sort_values('Ventas Totales', ascending=False)
        all_clients['Ventas Totales'] = all_clients['Ventas Totales'].apply(lambda x: f"${x:,.2f}")
        all_clients['Última Compra'] = all_clients['Última Compra'].dt.strftime('%d/%m/%Y')
        st.dataframe(all_clients.head(50), hide_index=True, use_container_width=True)
        return
    
    # Search for matching clients
    matching = df[df['cliente_nombre'].str.lower().str.contains(search_term.lower(), na=False)]
    unique_matches = matching['cliente_nombre'].unique()
    
    if len(unique_matches) == 0:
        st.warning(f"No se encontraron clientes con '{search_term}'")
        return
    
    st.success(f"Se encontraron {len(unique_matches)} cliente(s)")
    
    # If multiple matches, let user select
    if len(unique_matches) > 1:
        selected_client = st.selectbox("Seleccionar cliente:", unique_matches)
    else:
        selected_client = unique_matches[0]
    
    # Show client details
    client_df = df[df['cliente_nombre'] == selected_client]
    today = df['fecha'].max()
    
    st.subheader(f"📊 {selected_client}")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Comprado", f"${client_df['venta_neta'].sum():,.2f}")
    col2.metric("Transacciones", len(client_df['factura_id'].unique()))
    col3.metric("Última Compra", client_df['fecha'].max().strftime('%d/%m/%Y'))
    days_inactive = (today - client_df['fecha'].max()).days
    col4.metric("Días Sin Comprar", days_inactive, delta=f"{-days_inactive}" if days_inactive < 30 else None)
    
    st.markdown("---")
    
    # Products bought
    st.subheader("📦 Productos Comprados")
    products = client_df.groupby('producto').agg({
        'cantidad': 'sum',
        'venta_neta': 'sum',
        'fecha': 'max'
    }).reset_index().sort_values('venta_neta', ascending=False)
    products.columns = ['Producto', 'Cantidad', 'Valor', 'Última Compra']
    
    fig = px.bar(products.head(15), x='Valor', y='Producto', orientation='h', template='plotly_dark', color='Valor')
    fig.update_layout(yaxis={'categoryorder': 'total ascending'})
    st.plotly_chart(fig, use_container_width=True)
    
    st.dataframe(products.head(20), hide_index=True, use_container_width=True)


def render_product_search(search_term):
    """Search and display product details based on search term."""
    st.title("🔍 Buscador de Productos")
    
    if not search_term:
        st.info("👆 Ingresa el nombre de un producto en la barra lateral para buscarlo.")
        
        # Show all products as a list
        st.subheader("📋 Lista de Productos")
        all_products = df.groupby('producto').agg({
            'venta_neta': 'sum',
            'cantidad': 'sum',
            'cliente_nombre': 'nunique',
            'fecha': 'max'
        }).reset_index()
        all_products.columns = ['Producto', 'Ventas Totales', 'Unidades', 'Clientes', 'Última Venta']
        all_products = all_products.sort_values('Ventas Totales', ascending=False)
        all_products['Ventas Totales'] = all_products['Ventas Totales'].apply(lambda x: f"${x:,.2f}")
        all_products['Última Venta'] = all_products['Última Venta'].dt.strftime('%d/%m/%Y')
        st.dataframe(all_products.head(50), hide_index=True, use_container_width=True)
        return
    
    # Search for matching products
    matching = df[df['producto'].str.lower().str.contains(search_term.lower(), na=False)]
    unique_matches = matching['producto'].unique()
    
    if len(unique_matches) == 0:
        st.warning(f"No se encontraron productos con '{search_term}'")
        return
    
    st.success(f"Se encontraron {len(unique_matches)} producto(s)")
    
    # If multiple matches, let user select
    if len(unique_matches) > 1:
        selected_product = st.selectbox("Seleccionar producto:", unique_matches)
    else:
        selected_product = unique_matches[0]
    
    # Show product details
    product_df = df[df['producto'] == selected_product]
    today = df['fecha'].max()
    
    st.subheader(f"📦 {selected_product}")
    
    # Key metrics
    total_sales = product_df['venta_neta'].sum()
    total_units = product_df['cantidad'].sum()
    unique_customers = product_df['cliente_nombre'].nunique()
    last_sale = product_df['fecha'].max()
    days_since_sale = (today - last_sale).days
    avg_price = total_sales / total_units if total_units > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    with col1:
        styled_metric("Ventas Totales", f"${total_sales:,.2f}", delta=None)
    with col2:
        styled_metric("Unidades Vendidas", f"{total_units:,.0f}", delta=None)
    with col3:
        styled_metric("Clientes que Compran", str(unique_customers), delta=None)
    
    col4, col5, col6 = st.columns(3)
    with col4:
        styled_metric("Precio Promedio", f"${avg_price:,.2f}", delta=None)
    with col5:
        styled_metric("Última Venta", last_sale.strftime('%d/%m/%Y'), delta=None)
    with col6:
        styled_metric("Días Sin Vender", str(days_since_sale), 
                     delta=-days_since_sale if days_since_sale < 30 else days_since_sale,
                     delta_color="inverse" if days_since_sale > 0 else "normal")
    
    st.markdown("---")
    
    # Top customers for this product
    st.subheader("🏆 Top Clientes que Compran este Producto")
    customers = product_df.groupby('cliente_nombre').agg({
        'cantidad': 'sum',
        'venta_neta': 'sum',
        'fecha': ['max', 'count']
    }).reset_index()
    customers.columns = ['Cliente', 'Unidades', 'Total Comprado', 'Última Compra', 'Transacciones']
    customers = customers.sort_values('Total Comprado', ascending=False)
    
    # Chart
    fig = px.bar(customers.head(15), x='Total Comprado', y='Cliente', orientation='h', 
                 template='plotly_dark', color='Total Comprado',
                 color_continuous_scale='Blues')
    fig.update_layout(yaxis={'categoryorder': 'total ascending'}, title='Top 15 Clientes por Valor')
    st.plotly_chart(fig, use_container_width=True)
    
    # Table with all customers
    customers_display = customers.copy()
    customers_display['Total Comprado'] = customers_display['Total Comprado'].apply(lambda x: f"${x:,.2f}")
    customers_display['Última Compra'] = customers_display['Última Compra'].dt.strftime('%d/%m/%Y')
    st.dataframe(customers_display.head(30), hide_index=True, use_container_width=True)
    export_dataframe(customers, f"clientes_producto_{selected_product[:20]}", "product_customers")
    
    st.markdown("---")
    
    # Sales trend for this product
    st.subheader("📈 Tendencia de Ventas del Producto")
    monthly_sales = product_df.groupby(product_df['fecha'].dt.to_period('M')).agg({
        'venta_neta': 'sum',
        'cantidad': 'sum'
    }).reset_index()
    monthly_sales['fecha'] = monthly_sales['fecha'].dt.to_timestamp()
    
    fig = px.line(monthly_sales, x='fecha', y='venta_neta', markers=True, 
                  template='plotly_dark', title='Ventas Mensuales',
                  labels={'fecha': 'Mes', 'venta_neta': 'Ventas ($)'})
    st.plotly_chart(fig, use_container_width=True)


def render_inactive_clients():
    """Show inactive clients that need attention."""
    st.title("⏰ Clientes Inactivos")
    st.caption("Clientes importantes que no han comprado en más de 90 días")
    
    today = df['fecha'].max()
    
    cust_stats = df.groupby('cliente_nombre').agg({
        'venta_neta': 'sum',
        'fecha': ['max', 'count']
    }).reset_index()
    cust_stats.columns = ['cliente', 'total_ventas', 'ultima_compra', 'transacciones']
    cust_stats['dias_sin_compra'] = (today - cust_stats['ultima_compra']).dt.days
    
    # Filter important inactive
    important = cust_stats[(cust_stats['transacciones'] > 3) | (cust_stats['total_ventas'] > 5000)]
    inactive = important[important['dias_sin_compra'] > 90].sort_values('total_ventas', ascending=False)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Clientes Inactivos", len(inactive))
    col2.metric("Valor en Riesgo", f"${inactive['total_ventas'].sum():,.0f}")
    col3.metric("Días Promedio", f"{inactive['dias_sin_compra'].mean():.0f}")
    
    st.markdown("---")
    
    if not inactive.empty:
        fig = px.scatter(inactive, x='dias_sin_compra', y='total_ventas', 
                        hover_name='cliente', size='transacciones',
                        title='Clientes Inactivos: Días vs Valor',
                        template='plotly_dark', color='dias_sin_compra',
                        color_continuous_scale='Reds')
        st.plotly_chart(fig, use_container_width=True)
        
        inactive_display = inactive.copy()
        inactive_display['ultima_compra'] = inactive_display['ultima_compra'].dt.strftime('%d/%m/%Y')
        inactive_display['total_ventas'] = inactive_display['total_ventas'].apply(lambda x: f"${x:,.2f}")
        inactive_display.columns = ['Cliente', 'Ventas Totales', 'Última Compra', 'Transacciones', 'Días Inactivo']
        st.dataframe(inactive_display, hide_index=True, use_container_width=True)
    else:
        st.success("✅ No hay clientes importantes inactivos")


def render_top_products():
    """Show top performing products."""
    st.title("🏆 Top Productos")
    
    prod_stats = filtered_df.groupby('producto').agg({
        'venta_neta': 'sum',
        'cantidad': 'sum',
        'cliente_nombre': 'nunique',
        'fecha': ['max', 'count']
    }).reset_index()
    prod_stats.columns = ['Producto', 'Ventas', 'Cantidad', 'Clientes', 'Última Venta', 'Transacciones']
    prod_stats = prod_stats.sort_values('Ventas', ascending=False)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Productos", len(prod_stats))
    col2.metric("Top Producto", prod_stats.iloc[0]['Producto'][:20] + "...")
    col3.metric("Ventas #1", f"${prod_stats.iloc[0]['Ventas']:,.0f}")
    
    st.markdown("---")
    
    top_20 = prod_stats.head(20)
    fig = px.bar(top_20, x='Ventas', y='Producto', orientation='h',
                 template='plotly_dark', color='Ventas', color_continuous_scale='Blues')
    fig.update_layout(yaxis={'categoryorder': 'total ascending'})
    st.plotly_chart(fig, use_container_width=True)
    
    st.dataframe(prod_stats.head(30), hide_index=True, use_container_width=True)


def render_stale_products():
    """Show products without recent sales."""
    st.title("📉 Productos Sin Movimiento")
    st.caption("Productos importantes que no se han vendido en más de 60 días")
    
    today = df['fecha'].max()
    
    prod_stats = df.groupby('producto').agg({
        'venta_neta': 'sum',
        'fecha': ['max', 'count']
    }).reset_index()
    prod_stats.columns = ['producto', 'total_ventas', 'ultima_venta', 'transacciones']
    prod_stats['dias_sin_venta'] = (today - prod_stats['ultima_venta']).dt.days
    
    # Top 50 products by sales that are stale
    top_products = prod_stats.nlargest(50, 'total_ventas')
    stale = top_products[top_products['dias_sin_venta'] > 60].sort_values('total_ventas', ascending=False)
    
    col1, col2 = st.columns(2)
    col1.metric("Productos Afectados", len(stale))
    col2.metric("Ventas Históricas", f"${stale['total_ventas'].sum():,.0f}")
    
    st.markdown("---")
    
    if not stale.empty:
        fig = px.bar(stale.head(15), x='total_ventas', y='producto', orientation='h',
                     template='plotly_dark', color='dias_sin_venta', 
                     color_continuous_scale='Reds',
                     title='Productos Top Sin Ventas Recientes')
        fig.update_layout(yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig, use_container_width=True)
        
        stale_display = stale.copy()
        stale_display['ultima_venta'] = stale_display['ultima_venta'].dt.strftime('%d/%m/%Y')
        stale_display['total_ventas'] = stale_display['total_ventas'].apply(lambda x: f"${x:,.2f}")
        st.dataframe(stale_display, hide_index=True, use_container_width=True)
    else:
        st.success("✅ Todos los productos top tienen ventas recientes")


def render_ml_predictions():
    """ML-based sales predictions using Prophet for better seasonality handling."""
    st.title("🔮 Predicción de Ventas con Prophet")
    st.caption("Modelo avanzado que captura tendencia y estacionalidad automáticamente")
    
    # Model selection
    model_type = st.radio("Seleccionar modelo:", ["🚀 Prophet (Recomendado)", "📈 Regresión Lineal (Simple)"], horizontal=True)
    
    # Prepare monthly data
    monthly = df.groupby(df['fecha'].dt.to_period('M')).agg({
        'venta_neta': 'sum'
    }).reset_index()
    monthly['fecha'] = monthly['fecha'].dt.to_timestamp()
    
    if len(monthly) < 3:
        st.warning("Se necesitan al menos 3 meses de datos para hacer predicciones")
        return
    
    current_month_sales = monthly.iloc[-1]['venta_neta']
    
    if "Prophet" in model_type:
        try:
            from prophet import Prophet
            import numpy as np
        except ImportError:
            st.error("⚠️ Prophet no está instalado. Usando regresión lineal como fallback.")
            model_type = "Regresión Lineal"
    
    if "Prophet" in model_type:
        # Prophet requires specific column names
        prophet_df = monthly[['fecha', 'venta_neta']].copy()
        prophet_df.columns = ['ds', 'y']
        
        # Fit Prophet model with confidence intervals
        model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=False,
            daily_seasonality=False,
            interval_width=0.80  # 80% confidence interval (narrower bands)
        )
        model.fit(prophet_df)
        
        # Make future predictions
        future = model.make_future_dataframe(periods=3, freq='MS')
        forecast = model.predict(future)
        
        # Get predictions with confidence intervals
        future_preds = forecast.tail(3)
        pred_1 = future_preds.iloc[0]['yhat']
        pred_2 = future_preds.iloc[1]['yhat']
        pred_3 = future_preds.iloc[2]['yhat']
        
        # Confidence intervals
        ci_lower_1 = future_preds.iloc[0]['yhat_lower']
        ci_upper_1 = future_preds.iloc[0]['yhat_upper']
        
        # Calculate metrics on training data
        train_preds = forecast.head(len(monthly))
        y_true = monthly['venta_neta'].values
        y_pred = train_preds['yhat'].values
        
        # MAPE and MAE
        mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100
        mae = np.mean(np.abs(y_true - y_pred))
        
        change_pct = ((pred_1 - current_month_sales) / current_month_sales) * 100
        
        # Display metrics with styled cards
        st.markdown("### 📊 Métricas del Modelo Prophet")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            styled_metric("MAPE (Error %)", f"{mape:.1f}%", delta=-mape if mape < 20 else mape, delta_color="inverse")
        with col2:
            styled_metric("MAE (Error $)", f"${mae:,.0f}", delta=None)
        with col3:
            styled_metric("Mes Actual", f"${current_month_sales:,.0f}", delta=None)
        with col4:
            styled_metric("Predicción Próx. Mes", f"${pred_1:,.0f}", delta=change_pct)
        
        st.markdown("---")
        
        # Prediction table with confidence intervals
        st.subheader("🗓️ Proyecciones con Intervalos de Confianza (80%)")
        pred_df = pd.DataFrame({
            'Mes': ['Próximo Mes', 'En 2 Meses', 'En 3 Meses'],
            'Predicción': [f"${pred_1:,.0f}", f"${pred_2:,.0f}", f"${pred_3:,.0f}"],
            'Rango Inferior': [f"${future_preds.iloc[i]['yhat_lower']:,.0f}" for i in range(3)],
            'Rango Superior': [f"${future_preds.iloc[i]['yhat_upper']:,.0f}" for i in range(3)],
            'vs Actual': [f"{((future_preds.iloc[i]['yhat'] - current_month_sales) / current_month_sales * 100):+.1f}%" for i in range(3)]
        })
        st.dataframe(pred_df, hide_index=True, use_container_width=True)
        export_dataframe(pred_df, "predicciones_ventas", "pred_ventas")
        
        st.markdown("---")
        
        # Chart with confidence band
        st.subheader("📈 Tendencia, Estacionalidad y Proyección")
        
        fig = px.line(template='plotly_dark')
        
        # Historical data
        fig.add_scatter(x=monthly['fecha'], y=monthly['venta_neta'], 
                       mode='lines+markers', name='Ventas Reales', line=dict(color='#00d4aa'))
        
        # Predictions with confidence band
        fig.add_scatter(x=forecast['ds'], y=forecast['yhat'], 
                       mode='lines', name='Predicción', line=dict(color='#ff6b6b'))
        
        # Confidence band
        fig.add_scatter(x=forecast['ds'], y=forecast['yhat_upper'],
                       mode='lines', name='Límite Superior', line=dict(dash='dash', color='rgba(255,107,107,0.3)'))
        fig.add_scatter(x=forecast['ds'], y=forecast['yhat_lower'],
                       mode='lines', name='Límite Inferior', line=dict(dash='dash', color='rgba(255,107,107,0.3)'),
                       fill='tonexty', fillcolor='rgba(255,107,107,0.1)')
        
        fig.update_layout(title='Ventas Mensuales + Proyección con Intervalo de Confianza 80%',
                         xaxis_title='Fecha', yaxis_title='Ventas ($)')
        st.plotly_chart(fig, use_container_width=True)
        
        # Model explanation
        show_model_explanation(
            "Prophet (Facebook)",
            """
            Prophet es un modelo de series temporales desarrollado por Facebook/Meta que:
            - Detecta automáticamente tendencia y estacionalidad
            - Maneja datos faltantes y outliers
            - Proporciona intervalos de confianza
            - Es robusto para datos de negocio con patrones anuales
            """,
            {"MAPE": f"{mape:.1f}%", "MAE": f"${mae:,.0f}"},
            "Un MAPE < 20% indica buena precisión. El intervalo de confianza muestra el rango donde probablemente estarán las ventas reales."
        )
        
    else:
        # Fallback to linear regression
        from sklearn.linear_model import LinearRegression
        import numpy as np
        
        monthly['month_num'] = range(1, len(monthly) + 1)
        X = monthly['month_num'].values.reshape(-1, 1)
        y = monthly['venta_neta'].values
        
        model = LinearRegression()
        model.fit(X, y)
        
        pred_1 = model.predict([[len(monthly) + 1]])[0]
        pred_2 = model.predict([[len(monthly) + 2]])[0]
        pred_3 = model.predict([[len(monthly) + 3]])[0]
        
        r2 = model.score(X, y)
        y_pred = model.predict(X)
        mae = np.mean(np.abs(y - y_pred))
        
        change_pct = ((pred_1 - current_month_sales) / current_month_sales) * 100
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("R² Score", f"{r2:.2%}")
        col2.metric("MAE", f"${mae:,.0f}")
        col3.metric("Mes Actual", f"${current_month_sales:,.0f}")
        col4.metric("Predicción Próx. Mes", f"${pred_1:,.0f}", delta=f"{change_pct:+.1f}%")
        
        st.info("💡 La regresión lineal es más simple pero no captura estacionalidad. Considera usar Prophet para mejores resultados.")


# --- ADDITIONAL ML FUNCTIONS ---

def render_churn_prediction():
    """Predict which customers are at risk of churning."""
    st.title("📉 Predicción de Churn (Riesgo de Pérdida)")
    st.caption("Identifica clientes con alta probabilidad de dejar de comprar")
    
    try:
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.preprocessing import StandardScaler
        import numpy as np
    except ImportError:
        st.error("⚠️ scikit-learn no está instalado")
        return
    
    today = df['fecha'].max()
    
    # Build customer features
    cust_stats = df.groupby('cliente_nombre').agg({
        'venta_neta': ['sum', 'mean', 'std'],
        'fecha': ['max', 'min', 'count'],
        'cantidad': 'sum',
        'producto': 'nunique'
    }).reset_index()
    cust_stats.columns = ['cliente', 'total_ventas', 'venta_promedio', 'venta_std', 
                          'ultima_compra', 'primera_compra', 'transacciones', 
                          'cantidad', 'productos_unicos']
    
    cust_stats['dias_sin_compra'] = (today - cust_stats['ultima_compra']).dt.days
    cust_stats['dias_como_cliente'] = (cust_stats['ultima_compra'] - cust_stats['primera_compra']).dt.days
    cust_stats['frecuencia'] = cust_stats['transacciones'] / (cust_stats['dias_como_cliente'] + 1) * 30
    cust_stats['venta_std'] = cust_stats['venta_std'].fillna(0)
    
    # Define churn: no purchase in 90+ days AND was previously active (>3 transactions)
    cust_stats['churned'] = ((cust_stats['dias_sin_compra'] > 90) & (cust_stats['transacciones'] > 3)).astype(int)
    
    # Features for prediction
    feature_cols = ['total_ventas', 'venta_promedio', 'transacciones', 'productos_unicos', 'frecuencia']
    X = cust_stats[feature_cols].fillna(0)
    y = cust_stats['churned']
    
    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Train model
    model = RandomForestClassifier(n_estimators=50, random_state=42, max_depth=5)
    model.fit(X_scaled, y)
    
    # Calculate AUC if we have both classes
    from sklearn.metrics import roc_auc_score, accuracy_score
    y_pred = model.predict(X_scaled)
    y_proba = model.predict_proba(X_scaled)[:, 1]
    
    if len(np.unique(y)) > 1:
        auc_score = roc_auc_score(y, y_proba)
    else:
        auc_score = None
    
    accuracy = accuracy_score(y, y_pred)
    
    # Predict probability
    cust_stats['prob_churn'] = y_proba
    cust_stats['riesgo'] = pd.cut(cust_stats['prob_churn'], 
                                   bins=[0, 0.3, 0.6, 1.0], 
                                   labels=['🟢 Bajo', '🟡 Medio', '🔴 Alto'])
    
    # Display metrics
    high_risk = cust_stats[cust_stats['prob_churn'] > 0.6]
    
    st.markdown("### 📊 Métricas del Modelo")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if auc_score:
            styled_metric("AUC Score", f"{auc_score:.2f}", delta=(auc_score - 0.5) * 100 if auc_score > 0.5 else 0)
        else:
            st.metric("AUC Score", "N/A")
    with col2:
        styled_metric("Accuracy", f"{accuracy:.0%}", delta=None)
    with col3:
        styled_metric("Alto Riesgo", str(len(high_risk)), delta=len(high_risk)/len(cust_stats)*100, delta_color="inverse")
    with col4:
        styled_metric("Valor en Riesgo", f"${high_risk['total_ventas'].sum():,.0f}", delta=None)
    
    st.markdown("---")
    
    # Feature importance
    st.subheader("🔍 Importancia de Variables")
    importance_df = pd.DataFrame({
        'Variable': ['Ventas Totales', 'Venta Promedio', 'Transacciones', 'Productos Únicos', 'Frecuencia'],
        'Importancia': model.feature_importances_
    }).sort_values('Importancia', ascending=True)
    
    fig = px.bar(importance_df, x='Importancia', y='Variable', orientation='h',
                 template='plotly_dark', color='Importancia', color_continuous_scale='RdYlGn_r')
    fig.update_layout(title='¿Qué factores predicen el abandono?')
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Risk distribution
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("📊 Distribución de Riesgo")
        risk_counts = cust_stats['riesgo'].value_counts().reset_index()
        risk_counts.columns = ['Riesgo', 'Clientes']
        fig = px.pie(risk_counts, values='Clientes', names='Riesgo', 
                     template='plotly_dark',
                     color_discrete_map={'🟢 Bajo': '#00cc96', '🟡 Medio': '#ffa500', '🔴 Alto': '#ef553b'})
        st.plotly_chart(fig, use_container_width=True)
    
    with col_right:
        st.subheader("💰 Valor por Nivel de Riesgo")
        risk_value = cust_stats.groupby('riesgo')['total_ventas'].sum().reset_index()
        fig = px.bar(risk_value, x='riesgo', y='total_ventas', template='plotly_dark',
                     color='riesgo', color_discrete_map={'🟢 Bajo': '#00cc96', '🟡 Medio': '#ffa500', '🔴 Alto': '#ef553b'})
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Model explanation
    show_model_explanation(
        "Random Forest Classifier",
        """
        Random Forest es un modelo de clasificación que combina múltiples árboles de decisión:
        - Cada árbol vota sobre si un cliente va a abandonar
        - La probabilidad final es el promedio de todos los votos
        - Es robusto al ruido y no requiere escalado de variables
        """,
        {"AUC": f"{auc_score:.2f}" if auc_score else "N/A", "Accuracy": f"{accuracy:.0%}"},
        "Un AUC > 0.7 indica buen poder predictivo. La gráfica de importancia muestra qué variables más influyen en detectar abandono."
    )
    
    st.markdown("---")
    
    # Risk level filter
    st.subheader("🔍 Filtrar Clientes por Nivel de Riesgo")
    risk_filter = st.selectbox(
        "Mostrar clientes con riesgo:",
        ["🔴 Alto", "🟡 Medio", "🟢 Bajo", "Todos"],
        key="churn_risk_filter"
    )
    
    if risk_filter == "Todos":
        filtered_customers = cust_stats.copy()
    else:
        filtered_customers = cust_stats[cust_stats['riesgo'] == risk_filter].copy()
    
    st.subheader(f"📋 Clientes ({risk_filter}) - {len(filtered_customers)} encontrados")
    display_df = filtered_customers.nlargest(50, 'total_ventas')[['cliente', 'total_ventas', 'transacciones', 'dias_sin_compra', 'prob_churn', 'riesgo']].copy()
    export_df = display_df.copy()
    display_df['total_ventas'] = display_df['total_ventas'].apply(lambda x: f"${x:,.0f}")
    display_df['prob_churn'] = display_df['prob_churn'].apply(lambda x: f"{x:.0%}")
    display_df.columns = ['Cliente', 'Ventas Totales', 'Transacciones', 'Días Inactivo', 'Prob. Churn', 'Nivel Riesgo']
    st.dataframe(display_df, hide_index=True, use_container_width=True)
    export_dataframe(export_df, f"clientes_riesgo_{risk_filter.replace(' ', '_')}", "churn_export")


def render_product_associations():
    """Find products that are frequently bought together."""
    st.title("🛒 Productos que se Compran Juntos")
    st.caption("Análisis de asociación para cross-selling")
    
    # Group by invoice to find co-purchases
    invoice_products = df.groupby('factura_id')['producto'].apply(list).reset_index()
    
    # Count co-occurrences
    from collections import defaultdict
    cooccurrence = defaultdict(int)
    product_counts = defaultdict(int)
    
    for products in invoice_products['producto']:
        unique_products = list(set(products))
        for p in unique_products:
            product_counts[p] += 1
        for i, p1 in enumerate(unique_products):
            for p2 in unique_products[i+1:]:
                pair = tuple(sorted([p1, p2]))
                cooccurrence[pair] += 1
    
    # Convert to dataframe
    pairs_data = []
    for (p1, p2), count in cooccurrence.items():
        if count >= 2:  # Minimum 2 co-occurrences
            support = count / len(invoice_products)
            confidence_1 = count / product_counts[p1] if product_counts[p1] > 0 else 0
            confidence_2 = count / product_counts[p2] if product_counts[p2] > 0 else 0
            pairs_data.append({
                'producto_1': p1,
                'producto_2': p2,
                'veces_juntos': count,
                'soporte': support,
                'confianza': max(confidence_1, confidence_2)
            })
    
    pairs_df = pd.DataFrame(pairs_data).sort_values('veces_juntos', ascending=False)
    
    if pairs_df.empty:
        st.warning("No se encontraron suficientes asociaciones de productos")
        return
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Pares Encontrados", len(pairs_df))
    col2.metric("Par Más Frecuente", f"{pairs_df.iloc[0]['veces_juntos']} veces")
    col3.metric("Mejor Confianza", f"{pairs_df['confianza'].max():.0%}")
    
    st.markdown("---")
    
    # Top pairs
    st.subheader("🔗 Top 30 Pares de Productos")
    top_pairs = pairs_df.head(30).copy()
    top_pairs_export = top_pairs.copy()
    top_pairs['soporte'] = top_pairs['soporte'].apply(lambda x: f"{x:.1%}")
    top_pairs['confianza'] = top_pairs['confianza'].apply(lambda x: f"{x:.0%}")
    top_pairs.columns = ['Producto 1', 'Producto 2', 'Veces Juntos', 'Soporte', 'Confianza']
    st.dataframe(top_pairs, hide_index=True, use_container_width=True)
    export_dataframe(top_pairs_export, "pares_productos", "prod_pairs")
    
    st.markdown("---")
    
    # Product selector for recommendations
    st.subheader("🎯 Buscar Recomendaciones")
    all_products = sorted(df['producto'].unique())
    selected_product = st.selectbox("Selecciona un producto:", all_products, key="assoc_product")
    
    if selected_product:
        # Find top associated products
        associated = pairs_df[(pairs_df['producto_1'] == selected_product) | (pairs_df['producto_2'] == selected_product)].copy()
        if not associated.empty:
            associated['otro_producto'] = associated.apply(
                lambda x: x['producto_2'] if x['producto_1'] == selected_product else x['producto_1'], axis=1)
            associated = associated.nlargest(10, 'veces_juntos')
            
            st.success(f"**Clientes que compran '{selected_product[:30]}...' también compran:**")
            for _, row in associated.iterrows():
                st.write(f"• {row['otro_producto']} ({row['veces_juntos']} veces, {row['confianza']:.0%} confianza)")
        else:
            st.info("No se encontraron asociaciones significativas para este producto")


def render_product_demand():
    """Predict demand for each product."""
    st.title("📦 Predicción de Demanda por Producto")
    st.caption("Proyección de ventas para los próximos meses por producto")
    
    try:
        from sklearn.linear_model import LinearRegression
        import numpy as np
    except ImportError:
        st.error("⚠️ scikit-learn no está instalado")
        return
    
    # Get top products
    top_products = df.groupby('producto')['venta_neta'].sum().nlargest(20).index.tolist()
    
    selected_product = st.selectbox("Selecciona un producto:", top_products)
    
    if selected_product:
        prod_df = df[df['producto'] == selected_product]
        
        # Monthly sales for this product
        monthly = prod_df.groupby(prod_df['fecha'].dt.to_period('M')).agg({
            'venta_neta': 'sum',
            'cantidad': 'sum'
        }).reset_index()
        monthly['fecha'] = monthly['fecha'].astype(str)
        monthly['month_num'] = range(1, len(monthly) + 1)
        
        if len(monthly) < 3:
            st.warning("Se necesitan al menos 3 meses de datos")
            return
        
        # Train model
        X = monthly['month_num'].values.reshape(-1, 1)
        y = monthly['venta_neta'].values
        
        model = LinearRegression()
        model.fit(X, y)
        
        # Predictions
        next_months = [len(monthly) + i for i in range(1, 4)]
        predictions = [model.predict([[m]])[0] for m in next_months]
        
        current_sales = monthly.iloc[-1]['venta_neta']
        change_pct = ((predictions[0] - current_sales) / current_sales) * 100 if current_sales > 0 else 0
        r2 = model.score(X, y)
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Ventas Actual", f"${current_sales:,.0f}")
        col2.metric("Predicción Próx. Mes", f"${predictions[0]:,.0f}", delta=f"{change_pct:+.1f}%")
        col3.metric("Tendencia", "📈 Subiendo" if model.coef_[0] > 0 else "📉 Bajando")
        col4.metric("Confianza (R²)", f"{r2:.0%}")
        
        st.markdown("---")
        
        # Chart
        future_data = pd.DataFrame({
            'fecha': [f'Pred {i}' for i in range(1, 4)],
            'month_num': next_months,
            'venta_neta': predictions,
            'tipo': ['Predicción'] * 3
        })
        
        chart_data = monthly.copy()
        chart_data['tipo'] = 'Real'
        chart_data = pd.concat([chart_data, future_data], ignore_index=True)
        
        fig = px.line(chart_data, x='fecha', y='venta_neta', color='tipo', markers=True,
                      title=f'Ventas de {selected_product[:40]}',
                      template='plotly_dark',
                      color_discrete_map={'Real': '#00d4aa', 'Predicción': '#ff6b6b'})
        st.plotly_chart(fig, use_container_width=True)


def render_clv_prediction():
    """Predict Customer Lifetime Value."""
    st.title("💰 Valor de Vida del Cliente (CLV)")
    st.caption("Estimación del valor futuro de cada cliente")
    
    today = df['fecha'].max()
    
    # Calculate customer metrics
    cust_stats = df.groupby('cliente_nombre').agg({
        'venta_neta': ['sum', 'mean'],
        'fecha': ['max', 'min', 'count']
    }).reset_index()
    cust_stats.columns = ['cliente', 'total_ventas', 'venta_promedio', 'ultima_compra', 'primera_compra', 'transacciones']
    
    # Calculate CLV components
    cust_stats['dias_como_cliente'] = (cust_stats['ultima_compra'] - cust_stats['primera_compra']).dt.days + 1
    cust_stats['frecuencia_mensual'] = cust_stats['transacciones'] / (cust_stats['dias_como_cliente'] / 30)
    cust_stats['dias_sin_compra'] = (today - cust_stats['ultima_compra']).dt.days
    
    # Simple CLV: Average order value × Purchase frequency × Expected lifespan
    # Assuming 2 year expected lifespan for active customers
    cust_stats['clv_estimado'] = cust_stats['venta_promedio'] * cust_stats['frecuencia_mensual'] * 24
    
    # Adjust for inactive customers
    cust_stats.loc[cust_stats['dias_sin_compra'] > 180, 'clv_estimado'] *= 0.2
    cust_stats.loc[(cust_stats['dias_sin_compra'] > 90) & (cust_stats['dias_sin_compra'] <= 180), 'clv_estimado'] *= 0.5
    
    # Segment by CLV
    cust_stats['segmento_valor'] = pd.qcut(cust_stats['clv_estimado'], q=4, 
                                            labels=['💎 Platino', '🥇 Oro', '🥈 Plata', '🥉 Bronce'],
                                            duplicates='drop')
    
    # Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("CLV Promedio", f"${cust_stats['clv_estimado'].mean():,.0f}")
    col2.metric("CLV Máximo", f"${cust_stats['clv_estimado'].max():,.0f}")
    col3.metric("Valor Total Proyectado", f"${cust_stats['clv_estimado'].sum():,.0f}")
    
    st.markdown("---")
    
    # Distribution
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("📊 Distribución de CLV")
        fig = px.histogram(cust_stats, x='clv_estimado', nbins=30, template='plotly_dark',
                          labels={'clv_estimado': 'CLV Estimado ($)'})
        st.plotly_chart(fig, use_container_width=True)
    
    with col_right:
        st.subheader("🏆 Valor por Segmento")
        seg_stats = cust_stats.groupby('segmento_valor').agg({
            'cliente': 'count',
            'clv_estimado': 'sum'
        }).reset_index()
        seg_stats.columns = ['Segmento', 'Clientes', 'CLV Total']
        fig = px.bar(seg_stats, x='Segmento', y='CLV Total', template='plotly_dark', color='Segmento')
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Segment filter
    st.subheader("🔍 Filtrar Clientes por Nivel de Valor")
    segment_filter = st.selectbox(
        "Mostrar clientes del segmento:",
        ["💎 Platino", "🥇 Oro", "🥈 Plata", "🥉 Bronce", "Todos"],
        key="clv_segment_filter"
    )
    
    if segment_filter == "Todos":
        filtered_clv = cust_stats.copy()
    else:
        filtered_clv = cust_stats[cust_stats['segmento_valor'] == segment_filter].copy()
    
    st.subheader(f"📋 Clientes ({segment_filter}) - {len(filtered_clv)} encontrados")
    display_clv = filtered_clv.nlargest(50, 'clv_estimado')[['cliente', 'total_ventas', 'transacciones', 'frecuencia_mensual', 'clv_estimado', 'segmento_valor', 'dias_sin_compra']].copy()
    export_clv = display_clv.copy()
    display_clv['total_ventas'] = display_clv['total_ventas'].apply(lambda x: f"${x:,.0f}")
    display_clv['clv_estimado'] = display_clv['clv_estimado'].apply(lambda x: f"${x:,.0f}")
    display_clv['frecuencia_mensual'] = display_clv['frecuencia_mensual'].apply(lambda x: f"{x:.1f}")
    display_clv.columns = ['Cliente', 'Ventas Históricas', 'Trans.', 'Freq/Mes', 'CLV Estimado', 'Nivel', 'Días Inactivo']
    st.dataframe(display_clv, hide_index=True, use_container_width=True)
    export_dataframe(export_clv, f"clientes_clv_{segment_filter.replace(' ', '_')}", "clv_export")


def render_seasonality():
    """Analyze sales seasonality patterns."""
    st.title("🗓️ Análisis de Estacionalidad")
    st.caption("Patrones de ventas por mes, día de la semana y hora")
    
    df_season = df.copy()
    df_season['mes'] = df_season['fecha'].dt.month
    df_season['nombre_mes'] = df_season['fecha'].dt.month_name()
    df_season['dia_semana'] = df_season['fecha'].dt.dayofweek
    df_season['nombre_dia'] = df_season['fecha'].dt.day_name()
    df_season['semana_mes'] = (df_season['fecha'].dt.day - 1) // 7 + 1
    
    # Monthly pattern
    st.subheader("📅 Patrón Mensual")
    monthly = df_season.groupby(['mes', 'nombre_mes'])['venta_neta'].sum().reset_index()
    monthly = monthly.sort_values('mes')
    avg = monthly['venta_neta'].mean()
    monthly['status'] = monthly['venta_neta'].apply(
        lambda x: 'Alto' if x > avg * 1.1 else ('Bajo' if x < avg * 0.9 else 'Normal'))
    
    # Best/worst months
    best_month = monthly.loc[monthly['venta_neta'].idxmax(), 'nombre_mes']
    worst_month = monthly.loc[monthly['venta_neta'].idxmin(), 'nombre_mes']
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Mejor Mes", best_month)
    col2.metric("Peor Mes", worst_month)
    col3.metric("Variación", f"{((monthly['venta_neta'].max() - monthly['venta_neta'].min()) / avg * 100):.0f}%")
    
    fig = px.bar(monthly, x='nombre_mes', y='venta_neta', color='status',
                 template='plotly_dark',
                 color_discrete_map={'Alto': '#00cc96', 'Normal': '#636efa', 'Bajo': '#ef553b'})
    fig.add_hline(y=avg, line_dash="dash", line_color="yellow", annotation_text="Promedio")
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Day of week pattern
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("📆 Patrón por Día de Semana")
        daily = df_season.groupby(['dia_semana', 'nombre_dia'])['venta_neta'].sum().reset_index()
        daily = daily.sort_values('dia_semana')
        fig = px.bar(daily, x='nombre_dia', y='venta_neta', template='plotly_dark', color='venta_neta')
        st.plotly_chart(fig, use_container_width=True)
    
    with col_right:
        st.subheader("📈 Semana del Mes")
        weekly = df_season.groupby('semana_mes')['venta_neta'].sum().reset_index()
        weekly['semana_mes'] = weekly['semana_mes'].apply(lambda x: f"Semana {x}")
        fig = px.bar(weekly, x='semana_mes', y='venta_neta', template='plotly_dark', color='venta_neta')
        st.plotly_chart(fig, use_container_width=True)
    
    # Insights
    st.markdown("---")
    st.subheader("💡 Insights de Estacionalidad")
    
    best_day = daily.loc[daily['venta_neta'].idxmax(), 'nombre_dia']
    worst_day = daily.loc[daily['venta_neta'].idxmin(), 'nombre_dia']
    
    st.info(f"""
    **Hallazgos clave:**
    - 📈 **Mejor mes:** {best_month} (considerar aumentar inventario)
    - 📉 **Peor mes:** {worst_month} (buen momento para promociones)
    - 📅 **Mejor día:** {best_day}
    - 📅 **Peor día:** {worst_day}
    """)


def render_next_purchase():
    """Predict when customers will make their next purchase."""
    st.title("⏰ Predicción de Próxima Compra")
    st.caption("Estima cuándo volverá a comprar cada cliente")
    
    today = df['fecha'].max()
    
    # Calculate purchase intervals per customer
    def calc_avg_interval(group):
        if len(group) < 2:
            return None
        dates = group['fecha'].sort_values()
        intervals = dates.diff().dt.days.dropna()
        return intervals.mean() if len(intervals) > 0 else None
    
    cust_intervals = df.groupby('cliente_nombre').apply(calc_avg_interval).reset_index()
    cust_intervals.columns = ['cliente', 'intervalo_promedio']
    
    # Get last purchase date
    last_purchase = df.groupby('cliente_nombre')['fecha'].max().reset_index()
    last_purchase.columns = ['cliente', 'ultima_compra']
    
    # Merge
    cust_pred = cust_intervals.merge(last_purchase, on='cliente')
    cust_pred = cust_pred.dropna()
    
    # Calculate expected next purchase
    cust_pred['dias_desde_ultima'] = (today - cust_pred['ultima_compra']).dt.days
    cust_pred['dias_hasta_proxima'] = cust_pred['intervalo_promedio'] - cust_pred['dias_desde_ultima']
    cust_pred['fecha_esperada'] = cust_pred['ultima_compra'] + pd.to_timedelta(cust_pred['intervalo_promedio'], unit='D')
    cust_pred['estado'] = cust_pred['dias_hasta_proxima'].apply(
        lambda x: '🔴 Atrasado' if x < -7 else ('🟡 Próximo' if x < 7 else '🟢 A tiempo'))
    
    # Add total sales
    cust_sales = df.groupby('cliente_nombre')['venta_neta'].sum().reset_index()
    cust_sales.columns = ['cliente', 'total_ventas']
    cust_pred = cust_pred.merge(cust_sales, on='cliente')
    
    # Filter to active customers (max 180 days since last purchase, interval < 180 days)
    active = cust_pred[
        (cust_pred['intervalo_promedio'] < 180) & 
        (cust_pred['dias_desde_ultima'] <= 180)
    ].copy()
    
    # Metrics
    overdue = active[active['estado'] == '🔴 Atrasado']
    upcoming = active[active['estado'] == '🟡 Próximo']
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Clientes Analizados", len(active))
    col2.metric("Atrasados", len(overdue))
    col3.metric("Próximos (7 días)", len(upcoming))
    col4.metric("Intervalo Promedio", f"{active['intervalo_promedio'].mean():.0f} días")
    
    st.markdown("---")
    
    # Status distribution
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("📊 Estado de Compras")
        status_counts = active['estado'].value_counts().reset_index()
        status_counts.columns = ['Estado', 'Clientes']
        fig = px.pie(status_counts, values='Clientes', names='Estado', template='plotly_dark',
                     color_discrete_map={'🔴 Atrasado': '#ef553b', '🟡 Próximo': '#ffa500', '🟢 A tiempo': '#00cc96'})
        st.plotly_chart(fig, use_container_width=True)
    
    with col_right:
        st.subheader("📈 Distribución de Intervalos")
        fig = px.histogram(active, x='intervalo_promedio', nbins=20, template='plotly_dark',
                          labels={'intervalo_promedio': 'Días entre compras'})
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Overdue customers (prioritize by value)
    st.subheader("🚨 Clientes Atrasados (Ordenados por Valor)")
    if not overdue.empty:
        overdue_display = overdue.nlargest(20, 'total_ventas')[['cliente', 'total_ventas', 'intervalo_promedio', 'dias_desde_ultima', 'dias_hasta_proxima']].copy()
        overdue_display['total_ventas'] = overdue_display['total_ventas'].apply(lambda x: f"${x:,.0f}")
        overdue_display['intervalo_promedio'] = overdue_display['intervalo_promedio'].apply(lambda x: f"{x:.0f} días")
        overdue_display['dias_hasta_proxima'] = overdue_display['dias_hasta_proxima'].apply(lambda x: f"{abs(x):.0f} días atrasado")
        overdue_display.columns = ['Cliente', 'Ventas Totales', 'Intervalo Normal', 'Días Desde Última', 'Atraso']
        st.dataframe(overdue_display, hide_index=True, use_container_width=True)
    else:
        st.success("✅ No hay clientes atrasados")


# --- MAIN ROUTING ---

if selected_view == "📊 Visión General":
    render_overview()
elif selected_view == "📢 Recordatorios":
    render_reminders()
elif selected_view == "⚙️ Configuración":
    render_config()

# ML sub-sections
elif selected_view == "ML_📈 Ventas Futuras":
    render_ml_predictions()
elif selected_view == "ML_📉 Riesgo de Churn":
    render_churn_prediction()
elif selected_view == "ML_🛒 Productos Asociados":
    render_product_associations()
elif selected_view == "ML_📦 Demanda por Producto":
    render_product_demand()
elif selected_view == "ML_💰 Valor del Cliente":
    render_clv_prediction()
elif selected_view == "ML_🗓️ Estacionalidad":
    render_seasonality()
elif selected_view == "ML_⏰ Próxima Compra":
    render_next_purchase()

# Clientes sub-sections
elif selected_view == "Clientes_🔍 Buscador":
    render_client_search(client_search)
elif selected_view == "Clientes_👤 Explorador":
    render_customer_deep_dive()
elif selected_view == "Clientes_🎯 Segmentación RFM":
    render_rfm_segmentation()
elif selected_view == "Clientes_⏰ Inactivos":
    render_inactive_clients()

# Productos sub-sections
elif selected_view.startswith("Productos_"):
    # Check if product search is active
    if 'product_search' in dir() and product_search:
        render_product_search(product_search)
    elif selected_view == "Productos_🏆 Top Productos":
        render_top_products()
    elif selected_view == "Productos_📉 Sin Movimiento":
        render_stale_products()
    elif selected_view == "Productos_⏳ Análisis Recencia":
        render_recency_analysis()

# Categorías sub-sections
elif selected_view == "Categorías_📊 Por Categoría":
    render_category_analysis()
elif selected_view == "Categorías_📦 Agrupadas":
    render_grouped_category_analysis()
