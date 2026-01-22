import pandas as pd
import streamlit as st
import re
from thefuzz import process, fuzz
from product_catalog import CANONICAL_PRODUCTS

@st.cache_data
def load_data(file_path):
    """
    Loads sales data from a CSV file.
    """
    try:
        df = pd.read_csv(file_path, encoding='utf-8-sig')
        
        # Standardize column names (lowercase, strip spaces)
        df.columns = df.columns.str.strip().str.lower()
        
        # Parse Dates (DD/MM/YYYY)
        if 'fecha' in df.columns:
            df['fecha'] = pd.to_datetime(df['fecha'], format='%d/%m/%Y', errors='coerce')
            df['month_year'] = df['fecha'].dt.to_period('M')
        
        # Ensure numeric columns are numeric
        numeric_cols = ['venta_neta', 'cantidad', 'precio_unitario', 'total_linea', 'importetotal']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # Normalize Product Names
        if 'producto' in df.columns:
            df = normalize_products(df)
            
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()


def clean_str(s):
    """Clean string for matching (lowercase, remove symbols, remove colors)."""
    if not isinstance(s, str): return ""
    s = s.lower()
    
    # Remove noise words
    noise_words = ['tapiz', 'americano', 'importado', 'decorativo', 'textil', 'sintetico', 'bondeado']
    for word in noise_words:
        s = s.replace(word, '')
    
    # Remove all special chars first
    s = re.sub(r'[^a-z0-9\s]', ' ', s)
    
    # Remove color words entirely (Spanish and English)
    colors_to_remove = [
        'negro', 'black', 'noir',
        'azul', 'blue',
        'rojo', 'red',
        'gris', 'grey', 'gray',
        'blanco', 'white',
        'cafe', 'brown', 'marron',
        'verde', 'green',
        'plata', 'silver',
        'beige',
        'naranja', 'orange',
        'rosa', 'pink',
        'tabaco',
        'caramelo',
        'arena',
        'vino',
        'oscuro', 'dark',
        'claro', 'light',
    ]
    
    parts = s.split()
    parts = [p for p in parts if p not in colors_to_remove]
    
    return " ".join(parts)


def clean_display_str(s):
    """Clean string for display (removes symbols, Title Case)."""
    if not isinstance(s, str): return s
    s = re.sub(r'[^a-zA-Z0-9\s]', ' ', s)
    return " ".join(s.split()).title()


def normalize_products(df, threshold=85):
    """
    Normalizes product names using the master CANONICAL_PRODUCTS list.
    """
    # Group "Arrendamiento" variations
    df.loc[df['producto'].str.contains('ARRENDAMIENTO', case=False, na=False), 'producto'] = 'ARRENDAMIENTO'
    
    unique_products = df['producto'].dropna().unique()
    
    mapping = {}
    
    # Pre-clean the canonical list
    canonical_map = {clean_str(p): p for p in CANONICAL_PRODUCTS}
    canonical_cleaned_keys = list(canonical_map.keys())
    
    for name in unique_products:
        if name == 'ARRENDAMIENTO':
            mapping[name] = name
            continue
            
        cleaned_input = clean_str(name)
        
        # 1. Exact Match
        if cleaned_input in canonical_map:
            mapping[name] = canonical_map[cleaned_input]
            continue
            
        # 2. Fuzzy Match
        match = process.extractOne(cleaned_input, canonical_cleaned_keys, scorer=fuzz.ratio, score_cutoff=threshold)
        
        if match:
            mapping[name] = canonical_map[match[0]]
        else:
            # No match: clean the original for display
            mapping[name] = clean_display_str(name)

    df['producto_normalizado'] = df['producto'].map(mapping)
    df['producto_original'] = df['producto']
    df['producto'] = df['producto_normalizado']
    
    return df


def get_kpis(df):
    """Calculates basic KPIs."""
    total_revenue = df['venta_neta'].sum()
    total_orders = df['factura_id'].nunique()
    total_items = df['cantidad'].sum()
    avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
    
    return {
        "total_revenue": total_revenue,
        "total_orders": total_orders,
        "total_items": total_items,
        "avg_order_value": avg_order_value
    }
