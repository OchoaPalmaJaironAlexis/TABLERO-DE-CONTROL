import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import scipy.stats as stats

# ==========================================
# 1. CONFIGURACIÓN DE PÁGINA (UI/UX)
# ==========================================
st.set_page_config(
    page_title="HACCP Quality OS | Oceánica",
    page_icon="🦐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo CSS inyectado para FONDO AZUL PIZARRA (Dark Mode Suave)
st.markdown("""
    <style>
    /* Fondo principal de la aplicación */
    .stApp {
        background-color: #1e293b; 
    }
    /* Estilo de la barra lateral */
    [data-testid="stSidebar"] {
        background-color: #0f172a;
    }
    /* Tipografía global */
    h1, h2, h3, h4, h5, h6, p, span {
        color: #f1f5f9 !important; 
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    /* Tarjetas de KPI (Métricas) */
    .stMetric {
        background-color: #334155 !important; 
        padding: 15px; 
        border-radius: 8px; 
        border: 1px solid #475569;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
    }
    /* Color resaltado para los números de las métricas */
    [data-testid="stMetricValue"] {
        color: #38bdf8 !important; 
    }
    /* Ajuste de separadores */
    hr {
        border-color: #475569;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. MOTOR DE DATOS (CON CACHÉ EMPRESARIAL)
# ==========================================
@st.cache_data(show_spinner="Procesando base de datos...")
def load_data(file):
    try:
        df = pd.read_excel(file)
        if 'Fecha' in df.columns:
            df['Fecha'] = pd.to_datetime(df['Fecha'])
        return df
    except Exception as e:
        return None

# ==========================================
# 3. BARRA LATERAL (MENÚ PRINCIPAL)
# ==========================================
with st.sidebar:
    st.markdown("## **HACCP Quality OS**")
    st.markdown("---")
    
    st.markdown("### 📂 1. Origen de Datos")
    archivo_subido = st.file_uploader("Importar matriz de inspección (.xlsx)", type=["xlsx"])
    
    st.markdown("---")
    st.markdown("### ⚙️ 2. Filtros Globales")
    
if archivo_subido is None:
    st.title("🦐 Sistema Inteligente de Liberación de Lotes")
    st.info("👈 **Bienvenido al sistema.** Por favor, importe el archivo de inspección en el menú lateral para inicializar el motor analítico.")
    st.stop()

# Carga de datos
df = load_data(archivo_subido)
if df is None:
    st.error("Error al leer el archivo. Asegúrese de que sea un formato Excel válido.")
    st.stop()

# Filtros dinámicos en la barra lateral
if 'Mes' in df.columns:
    meses_disponibles = ["Histórico Completo"] + sorted(list(df['Mes'].dropna().unique()))
    mes_seleccionado = st.sidebar.selectbox("Filtro Temporal (Mes):", meses_disponibles)
    if mes_seleccionado != "Histórico Completo":
        df = df[df['Mes'] == mes_seleccionado]

if 'Proveedor' in df.columns:
    proveedores_disponibles = ["Todos los Proveedores"] + sorted(list(df['Proveedor'].dropna().unique()))
    proveedor_sel = st.sidebar.selectbox("Filtro por Proveedor:", proveedores_disponibles)
    if proveedor_sel != "Todos los Proveedores":
        df = df[df['Proveedor'] == proveedor_sel]

st.sidebar.markdown("---")
st.sidebar.caption("Oceánica HACCP System v2.1 | 2026")

# ==========================================
# 4. ENCABEZADO Y KPIS PRINCIPALES
# ==========================================
st.title("📊 Dashboard de Inteligencia de Calidad")
st.markdown("Monitoreo en tiempo real de tolerancias biológicas y fisicoquímicas.")

# Lógica de cálculo de KPIs
total_lotes = len(df)
if 'Estado_Lote' in df.columns:
    aprobados = len(df[df['Estado_Lote'] == 'APROBADO'])
    rechazados = len(df[df['Estado_Lote'] == 'RECHAZADO'])
    tasa_aprobacion = (aprobados / total_lotes) * 100 if total_lotes > 0 else 0
else:
    tasa_aprobacion, aprobados, rechazados = 0, 0, 0

temp_max = df['Temperatura_Arribo'].max() if 'Temperatura_Arribo' in df.columns else 0
melanosis_max = df['DM_Melanosis'].max() if 'DM_Melanosis' in df.columns else 0

# Renderizado de Tarjetas KPI
k1, k2, k3, k4 = st.columns(4)
k1.metric(label="Tasa de Aprobación", value=f"{tasa_aprobacion:.1f}%", delta=f"{aprobados} Lotes OK" if tasa_aprobacion > 80 else f"-{rechazados} Rechazados", delta_color="normal" if tasa_aprobacion > 80 else "inverse")

if temp_max <= 4.0:
    k2.metric(label="Temperatura Pico", value=f"{temp_max:.1f} °C", delta="Conforme (<4.0)", delta_color="normal")
else:
    k2.metric(label="Temperatura Pico", value=f"{temp_max:.1f} °C", delta="Brecha Crítica (>4.0)", delta_color="inverse")

if melanosis_max == 0:
    k3.metric(label="Incidencia Melanosis", value="0%", delta="Conforme", delta_color="normal")
else:
    k3.metric(label="Incidencia Melanosis", value=f"Alerta", delta="Violación Límite Cero", delta_color="inverse")

if 'Sulfito_Residual' in df.columns:
    sulfito_prom = df['Sulfito_Residual'].mean()
    k4.metric(label="Promedio Sulfito", value=f"{sulfito_prom:.0f} ppm", delta="Límite 100 ppm", delta_color="off")

st.markdown("---")

# ==========================================
# 5. ENRUTADOR DE PESTAÑAS (NAVEGACIÓN)
# ==========================================
tab1, tab2, tab3 = st.tabs(["📋 Resumen Ejecutivo", "📈 Control Estadístico (SPC)", "🔬 Análisis de Causa Raíz"])

# ------------------------------------------
# PESTAÑA 1: RESUMEN EJECUTIVO
# ------------------------------------------
with tab1:
    st.subheader("Estado General del Flujo de Recepción")
    colA, colB = st.columns([6, 4])
    
    with colA:
        if 'Proveedor' in df.columns and 'Estado_Lote' in df.columns:
            df_estado = df.groupby(['Proveedor', 'Estado_Lote']).size().reset_index(name='Cantidad')
            fig_prov = px.bar(df_estado, x='Proveedor', y='Cantidad', color='Estado_Lote', 
                              title="Rendimiento por Finca / Proveedor",
                              color_discrete_map={'APROBADO': '#2ecc71', 'RETENIDO': '#f1c40f', 'RECHAZADO': '#e74c3c'})
            fig_prov.update_layout(height=400, template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_prov, use_container_width=True)
        else:
            st.info("Faltan datos de 'Proveedor' o 'Estado_Lote' para este análisis.")

    with colB:
        if 'Uniformidad' in df.columns:
            uni_mean = df['Uniformidad'].mean()
            fig_gauge = go.Figure(go.Indicator(
                mode = "gauge+number", value = uni_mean,
                title = {'text': "Factor de Uniformidad Global", 'font': {'color': 'white'}},
                gauge = {
                    'axis': {'range': [1.0, 1.8], 'tickcolor': "white"},
                    'bar': {'color': "#38bdf8"},
                    'steps': [{'range': [1.0, 1.4], 'color': "#1e293b"}, {'range': [1.4, 1.8], 'color': "#475569"}],
                    'threshold': {'line': {'color': "#e74c3c", 'width': 4}, 'thickness': 0.75, 'value': 1.4}
                }))
            fig_gauge.update_layout(height=400, template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_gauge, use_container_width=True)

# ------------------------------------------
# PESTAÑA 2: CONTROL ESTADÍSTICO (SPC)
# ------------------------------------------
with tab2:
    st.subheader("Monitoreo de Variables Críticas (Inocuidad y Calidad)")
    
    if 'Temperatura_Arribo' in df.columns:
        fig_t = px.line(df, x='Lote' if 'Lote' in df.columns else df.index, y='Temperatura_Arribo', 
                        markers=True, title="Control de Temperatura de Arribo")
        fig_t.add_hrect(y0=0, y1=4, fillcolor="#2ecc71", opacity=0.1, line_width=0)
        # CORRECCIÓN DE LA ANOTACIÓN AL LÍMITE MÁXIMO
        fig_t.add_hline(y=4, line_dash="dash", line_color="#e74c3c", annotation_text="Límite Máximo Permitido (4°C)")
        fig_t.update_layout(height=350, template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', margin=dict(t=40, b=0))
        st.plotly_chart(fig_t, use_container_width=True)

    if 'Sulfito_Residual' in df.columns:
        y_data = df['Sulfito_Residual']
        m, sd = y_data.mean(), y_data.std()
        fig_s = go.Figure()
        
        # Datos principales
        fig_s.add_trace(go.Scatter(x=df['Lote'] if 'Lote' in df.columns else df.index, y=y_data, mode='lines+markers', name='PPM Sulfito', line=dict(color='#38bdf8')))
        
        # Línea de Media y Límite Legal
        fig_s.add_hline(y=m, line_color="#2ecc71", annotation_text="Media de Proceso")
        fig_s.add_hline(y=100, line_dash="solid", line_color="#e74c3c", annotation_text="Límite Legal Máximo (100 ppm)")
        
        # Límites de Control Superior (LSC) e Inferior (LIC)
        if not np.isnan(sd):
            fig_s.add_hline(y=m + 3*sd, line_dash="dot", line_color="#f39c12", annotation_text="LSC (+3σ)")
            fig_s.add_hline(y=max(0, m - 3*sd), line_dash="dot", line_color="#f39c12", annotation_text="LIC (-3σ)")
            
        fig_s.update_layout(title="Control Estadístico SPC: Sulfito Residual", height=350, template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', margin=dict(t=40, b=0))
        st.plotly_chart(fig_s, use_container_width=True)

# ------------------------------------------
# PESTAÑA 3: ANÁLISIS DE CAUSA RAÍZ
# ------------------------------------------
with tab3:
    st.subheader("Análisis de Defectos Físicos y Biológicos")
    
    colX, colY = st.columns(2)
    
    # PARETO DE DEFECTOS
    with colX:
        cols_defectos = [c for c in df.columns if c.startswith('DM_') or c.startswith('DMen_')]
        if cols_defectos:
            st.markdown("##### 📉 Priorización de Defectos (Pareto)")
            sum_defectos = df[cols_defectos].sum().sort_values(ascending=False)
            df_p = pd.DataFrame({'Defecto': sum_defectos.index, 'Impacto': sum_defectos.values})
            if df_p['Impacto'].sum() > 0:
                df_p['Acumulado'] = (df_p['Impacto'].cumsum() / df_p['Impacto'].sum()) * 100
                
                fig_p = make_subplots(specs=[[{"secondary_y": True}]])
                fig_p.add_trace(go.Bar(x=df_p['Defecto'], y=df_p['Impacto'], name="Impacto", marker_color='#38bdf8'), secondary_y=False)
                fig_p.add_trace(go.Scatter(x=df_p['Defecto'], y=df_p['Acumulado'], name="% Acumulado", mode='lines+markers', line=dict(color='#e74c3c', width=3)), secondary_y=True)
                fig_p.update_layout(height=450, template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', margin=dict(l=0, r=0, t=10, b=0), showlegend=False)
                fig_p.update_yaxes(range=[0, 105], secondary_y=True)
                st.plotly_chart(fig_p, use_container_width=True)
            else:
                st.success("No se registraron defectos en este periodo.")
        else:
            st.info("No se detectaron columnas de defectos (con prefijo DM_ o DMen_).")

    # DIAGRAMA DE DISPERSIÓN (REGRESIÓN)
    with colY:
        st.markdown("##### 🔍 Motor de Correlación Matemática")
        cols_num = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c]) and c not in ['Año', 'Mes', 'Semana', 'Día']]
        
        if len(cols_num) >= 2:
            cx1, cx2 = st.columns(2)
            var_x = cx1.selectbox("Variable Independiente (X):", cols_num, index=0)
            var_y = cx2.selectbox("Variable Dependiente (Y):", cols_num, index=1)
            
            mask = np.isfinite(df[var_x]) & np.isfinite(df[var_y])
            if mask.sum() > 2:
                r_pearson, _ = stats.pearsonr(df[var_x][mask], df[var_y][mask])
                if r_pearson > 0.7: diag = "Correlación Positiva Fuerte ↗️"
                elif r_pearson > 0.3: diag = "Correlación Positiva ↗️"
                elif r_pearson > -0.3: diag = "Sin Correlación 🔀"
                elif r_pearson > -0.7: diag = "Correlación Negativa ↘️"
                else: diag = "Correlación Negativa Fuerte ↘️"
                
                st.caption(f"**Diagnóstico:** {diag} | **Pearson (r):** {r_pearson:.2f}")
                
                fig_disp = px.scatter(df, x=var_x, y=var_y, trendline="ols", color='Proveedor' if 'Proveedor' in df.columns else None, color_discrete_sequence=px.colors.qualitative.Pastel)
                fig_disp.update_traces(marker=dict(size=8, opacity=0.8), selector=dict(mode='markers'))
                fig_disp.update_traces(line=dict(color='#e74c3c', width=4), selector=dict(mode='lines'))
                fig_disp.update_layout(height=350, template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', margin=dict(t=10, b=0))
                st.plotly_chart(fig_disp, use_container_width=True)
            else:
                st.warning("Datos insuficientes para calcular correlación.")
