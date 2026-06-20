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
    page_title="HACCP Process OS | Oceánica",
    page_icon="🦐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo CSS inyectado para FONDO AZUL PIZARRA (Dark Mode Suave)
st.markdown("""
    <style>
    .stApp { background-color: #1e293b; }
    [data-testid="stSidebar"] { background-color: #0f172a; }
    h1, h2, h3, h4, h5, h6, p, span { color: #f1f5f9 !important; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    .stMetric { background-color: #334155 !important; padding: 15px; border-radius: 8px; border: 1px solid #475569; box-shadow: 0 4px 6px rgba(0,0,0,0.2); }
    [data-testid="stMetricValue"] { color: #38bdf8 !important; }
    hr { border-color: #475569; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. MOTOR DE DATOS (CACHÉ EMPRESARIAL)
# ==========================================
@st.cache_data(show_spinner="Procesando métricas de planta...")
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
    st.markdown("## **HACCP Process OS**")
    st.markdown("---")
    
    st.markdown("### 📂 1. Alimentación de Datos")
    archivo_subido = st.file_uploader("Importar registro de planta (.xlsx)", type=["xlsx"])
    
    st.markdown("---")
    st.markdown("### ⚙️ 2. Filtros de Operación")
    
if archivo_subido is None:
    st.title("🏭 Sistema de Control de Procesos en Planta")
    st.info("👈 **Bienvenido al sistema.** Por favor, importe el archivo de inspección para inicializar la auditoría de procesos.")
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
    proveedor_sel = st.sidebar.selectbox("Auditoría por Proveedor:", proveedores_disponibles)
    if proveedor_sel != "Todos los Proveedores":
        df = df[df['Proveedor'] == proveedor_sel]

st.sidebar.markdown("---")
st.sidebar.caption("Oceánica Process Control v3.0 | 2026")

# ==========================================
# 4. ENCABEZADO Y KPIS PRINCIPALES
# ==========================================
st.title("📊 Dashboard de Control de Procesos (HACCP)")
st.markdown("Auditoría en tiempo real de las etapas de recepción, tratamiento químico, calibración y empaque.")

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
k1.metric(label="Rendimiento del Proceso (Yield)", value=f"{tasa_aprobacion:.1f}%", delta=f"{aprobados} Lotes Procesados", delta_color="normal" if tasa_aprobacion > 80 else "inverse")

if temp_max <= 4.0:
    k2.metric(label="Falla Crítica en Cadena de Frío", value=f"{temp_max:.1f} °C", delta="Logística Conforme (<4.0)", delta_color="normal")
else:
    k2.metric(label="Falla Crítica en Cadena de Frío", value=f"{temp_max:.1f} °C", delta="Alerta Logística (>4.0)", delta_color="inverse")

if melanosis_max == 0:
    k3.metric(label="Falla por Oxidación (Melanosis)", value="0%", delta="Tratamiento Conforme", delta_color="normal")
else:
    k3.metric(label="Falla por Oxidación (Melanosis)", value=f"Alerta", delta="Quiebre de Proceso", delta_color="inverse")

if 'Sulfito_Residual' in df.columns:
    sulfito_prom = df['Sulfito_Residual'].mean()
    k4.metric(label="Promedio Dosificación Química", value=f"{sulfito_prom:.0f} ppm", delta="Límite Operativo 100 ppm", delta_color="off")

st.markdown("---")

# ==========================================
# 5. ENRUTADOR DE PESTAÑAS (ENFOQUE DE PROCESOS)
# ==========================================
tab1, tab2, tab3 = st.tabs(["🏭 Visión Global de Operaciones", "❄️ Etapa 1 y 2: Logística y Tratamiento", "🦐 Etapa 3 y 4: Calibración y Empaque"])

# ------------------------------------------
# PESTAÑA 1: VISIÓN GLOBAL
# ------------------------------------------
with tab1:
    st.subheader("Auditoría General de Planta y Proveedores")
    colA, colB = st.columns([6, 4])
    
    with colA:
        if 'Proveedor' in df.columns and 'Estado_Lote' in df.columns:
            df_estado = df.groupby(['Proveedor', 'Estado_Lote']).size().reset_index(name='Cantidad')
            fig_prov = px.bar(df_estado, x='Proveedor', y='Cantidad', color='Estado_Lote', 
                              title="Eficiencia de Entrega por Finca",
                              color_discrete_map={'APROBADO': '#2ecc71', 'RETENIDO': '#f1c40f', 'RECHAZADO': '#e74c3c'})
            fig_prov.update_layout(height=400, template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_prov, use_container_width=True)
            st.caption("🔍 **Diagnóstico Operativo:** Mide la capacidad del proveedor para alinear sus procesos de cosecha con nuestros estándares.")

    with colB:
        if 'Uniformidad' in df.columns:
            uni_mean = df['Uniformidad'].mean()
            fig_gauge = go.Figure(go.Indicator(
                mode = "gauge+number", value = uni_mean,
                title = {'text': "Eficiencia de Maquinaria Clasificadora", 'font': {'color': 'white'}},
                gauge = {
                    'axis': {'range': [1.0, 1.8], 'tickcolor': "white"},
                    'bar': {'color': "#38bdf8"},
                    'steps': [{'range': [1.0, 1.4], 'color': "#1e293b"}, {'range': [1.4, 1.8], 'color': "#475569"}],
                    'threshold': {'line': {'color': "#e74c3c", 'width': 4}, 'thickness': 0.75, 'value': 1.4}
                }))
            fig_gauge.update_layout(height=400, template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_gauge, use_container_width=True)
            st.caption("🔍 **Diagnóstico Operativo:** Evalúa la precisión mecánica. Valores > 1.40 indican descalibración en los rodillos separadores.")

# ------------------------------------------
# PESTAÑA 2: LOGÍSTICA Y TRATAMIENTO
# ------------------------------------------
with tab2:
    st.subheader("Control Estadístico de Variables Físico-Químicas")
    
    if 'Temperatura_Arribo' in df.columns:
        st.info("💡 **Proceso Auditado (Recepción Logística):** Este gráfico no evalúa al producto en sí, sino la eficiencia de los contenedores isotérmicos y el manejo de hielo desde la cosecha hasta el andén de descarga.")
        fig_t = px.line(df, x='Lote' if 'Lote' in df.columns else df.index, y='Temperatura_Arribo', 
                        markers=True, title="Desempeño de la Cadena de Frío (Temp. Arribo)")
        fig_t.add_hrect(y0=0, y1=4, fillcolor="#2ecc71", opacity=0.1, line_width=0)
        fig_t.add_hline(y=4, line_dash="dash", line_color="#e74c3c", annotation_text="Límite Máximo Permitido (4°C)")
        fig_t.update_layout(height=350, template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', margin=dict(t=40, b=0))
        st.plotly_chart(fig_t, use_container_width=True)

    st.markdown("---")

    if 'Sulfito_Residual' in df.columns:
        st.info("💡 **Proceso Auditado (Inmersión Química):** Controla directamente el trabajo del operario en la tina. Desviaciones amplias significan que no se están respetando los tiempos de remojo o la dosis de metabisulfito.")
        y_data = df['Sulfito_Residual']
        m, sd = y_data.mean(), y_data.std()
        fig_s = go.Figure()
        
        fig_s.add_trace(go.Scatter(x=df['Lote'] if 'Lote' in df.columns else df.index, y=y_data, mode='lines+markers', name='PPM Sulfito', line=dict(color='#38bdf8')))
        fig_s.add_hline(y=m, line_color="#2ecc71", annotation_text="Media de Operación")
        fig_s.add_hline(y=100, line_dash="solid", line_color="#e74c3c", annotation_text="Límite Legal Máximo (100 ppm)")
        
        if not np.isnan(sd):
            fig_s.add_hline(y=m + 3*sd, line_dash="dot", line_color="#f39c12", annotation_text="LSC (+3σ)")
            fig_s.add_hline(y=max(0, m - 3*sd), line_dash="dot", line_color="#f39c12", annotation_text="LIC (-3σ)")
            
        fig_s.update_layout(title="Estabilidad del Tratamiento Químico SPC", height=350, template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', margin=dict(t=40, b=0))
        st.plotly_chart(fig_s, use_container_width=True)

# ------------------------------------------
# PESTAÑA 3: CALIBRACIÓN Y EMPAQUE
# ------------------------------------------
with tab3:
    st.subheader("Auditoría de Daños por Manipulación y Procesamiento")
    
    colX, colY = st.columns(2)
    
    with colX:
        cols_defectos = [c for c in df.columns if c.startswith('DM_') or c.startswith('DMen_')]
        if cols_defectos:
            st.markdown("##### 📉 Tasa de Errores en Línea de Empaque (Pareto)")
            st.info("💡 **Análisis de Proceso:** Altos niveles de daños mecánicos (Antenas Rotas, Estropeado) revelan cuellos de botella físicos, caídas bruscas en las bandas o maltrato durante el empaque manual.")
            
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
                st.success("Operación limpia: No se registraron defectos.")

    with colY:
        st.markdown("##### 🔍 Motor Predictivo de Fallas (Correlación)")
        st.info("💡 **Análisis de Proceso:** Permite aislar matemáticamente relaciones causa-efecto en la planta. (Ej. Relacionar directamente si un alza de temperatura causa mayor nivel de producto blando).")
        
        cols_num = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c]) and c not in ['Año', 'Mes', 'Semana', 'Día']]
        
        if len(cols_num) >= 2:
            cx1, cx2 = st.columns(2)
            var_x = cx1.selectbox("Etapa / Variable Causa (X):", cols_num, index=0)
            var_y = cx2.selectbox("Efecto / Variable Respuesta (Y):", cols_num, index=1)
            
            mask = np.isfinite(df[var_x]) & np.isfinite(df[var_y])
            if mask.sum() > 2:
                r_pearson, _ = stats.pearsonr(df[var_x][mask], df[var_y][mask])
                if r_pearson > 0.7: diag = "Correlación Positiva Fuerte ↗️"
                elif r_pearson > 0.3: diag = "Correlación Positiva ↗️"
                elif r_pearson > -0.3: diag = "Sin Correlación 🔀"
                elif r_pearson > -0.7: diag = "Correlación Negativa ↘️"
                else: diag = "Correlación Negativa Fuerte ↘️"
                
                st.caption(f"**Diagnóstico Operativo:** {diag} | **Pearson (r):** {r_pearson:.2f}")
                
                fig_disp = px.scatter(df, x=var_x, y=var_y, trendline="ols", color='Proveedor' if 'Proveedor' in df.columns else None, color_discrete_sequence=px.colors.qualitative.Pastel)
                fig_disp.update_traces(marker=dict(size=8, opacity=0.8), selector=dict(mode='markers'))
                fig_disp.update_traces(line=dict(color='#e74c3c', width=4), selector=dict(mode='lines'))
                fig_disp.update_layout(height=350, template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', margin=dict(t=10, b=0))
                st.plotly_chart(fig_disp, use_container_width=True)
