import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import scipy.stats as stats

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Tablero SPC - Calidad", layout="wide", page_icon="🦐")

# --- TÍTULO PRINCIPAL ---
st.title("📊 Panel de Control Gerencial (HACCP)")
st.markdown("Plataforma interactiva para el análisis estadístico y liberación de lotes.")

# --- BARRA LATERAL (MENÚ DE CONTROLES) ---
st.sidebar.header("📂 1. Carga de Datos")
archivo_subido = st.sidebar.file_uploader("Sube tu archivo Excel", type=["xlsx", "xls"])

if archivo_subido is not None:
    # 1. Leer el archivo Excel
    df = pd.read_excel(archivo_subido)
    
    with st.expander("👁️ Ver Base de Datos Original", expanded=False):
        st.dataframe(df, use_container_width=True)

    # 2. Identificar columnas numéricas (excluyendo fechas/IDs)
    cols_excluidas = ['Año', 'Mes', 'Semana', 'Día', 'Lote']
    cols_numericas = [col for col in df.columns if col not in cols_excluidas and pd.api.types.is_numeric_dtype(df[col])]

    if not cols_numericas:
        st.error("No se encontraron variables numéricas analizables en el Excel.")
        st.stop()

    st.sidebar.header("🎯 2. Filtros de Trazabilidad")
    
    # Filtro de Mes
    meses_disponibles = ["Todo el Histórico"] + sorted(list(df['Mes'].dropna().unique())) if 'Mes' in df.columns else ["Todo el Histórico"]
    mes_seleccionado = st.sidebar.selectbox("Filtro por Mes:", meses_disponibles)
    
    # Agrupación de tiempo
    opciones_agrupacion = [col for col in ['Lote', 'Día', 'Semana', 'Mes'] if col in df.columns]
    agrupacion = st.sidebar.selectbox("Agrupar gráficos por:", opciones_agrupacion if opciones_agrupacion else df.columns[0])
    
    # --- CONFIGURACIÓN INDIVIDUAL DE GRÁFICOS Y VARIABLES ---
    st.sidebar.header("🛠️ 3. Configuración de Gráficos")

    # Configuración de Gráfico de Control
    t_control = st.sidebar.checkbox("Gráfico de Control (SPC)", value=True)
    var_control = None
    if t_control:
        var_control = st.sidebar.selectbox("Variable para Control SPC:", cols_numericas, key="spc_var")

    st.sidebar.markdown("---")
    
    # Configuración de Gráfico de Barras
    t_barras = st.sidebar.checkbox("Composición (Gráfico de Barras)", value=True)
    vars_barras = []
    if t_barras:
        default_bar = [cols_numericas[0]] if cols_numericas else []
        vars_barras = st.sidebar.multiselect("Variables para Barras:", cols_numericas, default=default_bar, key="bar_vars")

    st.sidebar.markdown("---")

    # Configuración de Diagrama de Pareto
    t_pareto = st.sidebar.checkbox("Diagrama de Pareto (80/20)", value=True)
    vars_pareto = []
    if t_pareto:
        vars_pareto = st.sidebar.multiselect("Defectos para Pareto:", cols_numericas, default=cols_numericas, key="pareto_vars")

    st.sidebar.markdown("---")

    # Configuración de Diagrama de Dispersión
    t_dispersion = st.sidebar.checkbox("Diagrama de Dispersión (Regresión)", value=True)
    var_disp_x = None
    var_disp_y = None
    if t_dispersion:
        var_disp_x = st.sidebar.selectbox("Variable X (Independiente):", cols_numericas, index=0, key="disp_x")
        var_disp_y = st.sidebar.selectbox("Variable Y (Dependiente):", cols_numericas, index=min(1, len(cols_numericas)-1), key="disp_y")

    # --- MOTOR LÓGICO Y FILTRADO ---
    df_filtro = df.copy()
    if mes_seleccionado != "Todo el Histórico":
        df_filtro = df_filtro[df_filtro['Mes'] == mes_seleccionado]
        
    if df_filtro.empty:
        st.error("No hay datos para el mes seleccionado.")
        st.stop()

    # Aplicar Agrupación para los gráficos secuenciales (Control y Barras)
    if agrupacion == 'Lote' or agrupacion not in df_filtro.columns:
        df_plot = df_filtro.copy()
        eje_x = agrupacion if agrupacion in df_filtro.columns else df_filtro.index
    else:
        # Agrupamos promediando todas las numéricas por seguridad
        df_plot = df_filtro.groupby(agrupacion)[cols_numericas].mean().reset_index()
        df_plot[agrupacion] = df_plot[agrupacion].astype(str)
        eje_x = agrupacion

    # --- SECCIÓN SUPERIOR: KPIs DINÁMICOS ---
    st.markdown("### 📌 Resumen de Indicadores Clave")
    variables_kpi = list(set([v for v in [var_control, var_disp_x, var_disp_y] if v] + vars_barras))[:4]
    if variables_kpi:
        cols_kpi = st.columns(len(variables_kpi))
        for i, var in enumerate(variables_kpi):
            media_actual = df_plot[var].mean()
            cols_kpi[i].metric(label=f"Promedio: {var}", value=f"{media_actual:.2f}")
    st.divider()

    # --- SECCIÓN CENTRAL: DISTRIBUCIÓN DE PANTALLA ---
    col1, col2 = st.columns(2)

    # 1. GRÁFICO DE CONTROL SPC
    if t_control and var_control:
        with col1:
            st.subheader(f"🎯 Gráfico de Control SPC: {var_control}")
            fig_spc = go.Figure()
            y_data = df_plot[var_control]
            media, desv = y_data.mean(), y_data.std()
            
            fig_spc.add_trace(go.Scatter(x=df_plot[eje_x], y=y_data, mode='lines+markers', name='Datos', line=dict(color='#2980b9')))
            if not np.isnan(media) and not np.isnan(desv):
                fig_spc.add_hline(y=media, line_color="green", annotation_text="Media Global")
                fig_spc.add_hline(y=media + 3*desv, line_color="red", line_dash="dash", annotation_text="LSC (+3σ)")
                fig_spc.add_hline(y=max(0, media - 3*desv), line_color="red", line_dash="dash", annotation_text="LIC (-3σ)")
            
            fig_spc.update_layout(height=400, margin=dict(l=0, r=0, t=30, b=0), template="plotly_white")
            st.plotly_chart(fig_spc, use_container_width=True)

    # 2. GRÁFICO DE BARRAS COMPUESTAS
    if t_barras and vars_barras:
        with col2:
            st.subheader("📊 Composición General Analizada")
            fig_bar = px.bar(df_plot, x=eje_x, y=vars_barras, color_discrete_sequence=px.colors.qualitative.Pastel)
            fig_bar.update_layout(height=400, barmode='stack', margin=dict(l=0, r=0, t=30, b=0), template="plotly_white")
            st.plotly_chart(fig_bar, use_container_width=True)

    # NUEVA FILA DE GRÁFICOS
    col3, col2_full = st.columns([1, 1])

    # 3. DIAGRAMA DE PARETO
    if t_pareto and vars_pareto:
        with col3:
            st.divider()
            st.subheader("📈 Diagrama de Pareto de Defectos")
            promedios = {var: df_filtro[var].mean() for var in vars_pareto}
            df_p = pd.DataFrame(list(promedios.items()), columns=['Var', 'Val']).sort_values(by='Val', ascending=False)
            if df_p['Val'].sum() > 0:
                df_p['Cum'] = (df_p['Val'].cumsum() / df_p['Val'].sum()) * 100
                fig_p = make_subplots(specs=[[{"secondary_y": True}]])
                fig_p.add_trace(go.Bar(x=df_p['Var'], y=df_p['Val'], name="Impacto", marker_color='#2c3e50'), secondary_y=False)
                fig_p.add_trace(go.Scatter(x=df_p['Var'], y=df_p['Cum'], name="% Acum", mode='lines+markers', line=dict(color='#e74c3c', width=3)), secondary_y=True)
                fig_p.update_layout(height=400, margin=dict(l=0, r=0, t=30, b=0), template="plotly_white", showlegend=False)
                fig_p.update_yaxes(range=[0, 105], secondary_y=True)
                st.plotly_chart(fig_p, use_container_width=True)
            else:
                st.warning("No hay valores suficientes para calcular el Pareto.")

    # 4. DIAGRAMA DE DISPERSIÓN CON REGRESIÓN
    if t_dispersion and var_disp_x and var_disp_y:
        with col2_full:
            st.divider()
            st.subheader(f"🔍 Análisis de Correlación: {var_disp_x} vs {var_disp_y}")
            
            # Calcular correlación de Pearson sobre los datos filtrados
            mask = np.isfinite(df_filtro[var_disp_x]) & np.isfinite(df_filtro[var_disp_y])
            r_pearson = 0
            diagnostico = "Datos insuficientes"
            
            if mask.sum() > 2:
                r_pearson, _ = stats.pearsonr(df_filtro[var_disp_x][mask], df_filtro[var_disp_y][mask])
                if r_pearson > 0.7: diagnostico = "Correlación Positiva Evidente ↗️"
                elif r_pearson > 0.3: diagnostico = "Correlación Positiva ↗️"
                elif r_pearson > -0.3: diagnostico = "Sin Correlación 🔀"
                elif r_pearson > -0.7: diagnostico = "Correlación Negativa ↘️"
                else: diagnostico = "Correlación Negativa Evidente ↘️"

            # Mostrar bloques de diagnóstico debajo del título de la sección
            c_box1, c_box2 = st.columns(2)
            c_box1.info(f"**Patrón:** {diagnostico}")
            c_box2.info(f"**Coeficiente r:** {r_pearson:.3f}")

            # Color estático oscuro para las muestras y regresión en rojo brillante
            color_by = agrupacion if agrupacion in df_filtro.columns else None
            fig_disp = px.scatter(df_filtro, x=var_disp_x, y=var_disp_y, color=color_by, trendline="ols",
                                  color_continuous_scale='Viridis')
            
            fig_disp.update_traces(marker=dict(size=9, opacity=0.75), selector=dict(mode='markers'))
            fig_disp.update_traces(line=dict(color='red', width=4), selector=dict(mode='lines'))
            fig_disp.update_layout(height=400, margin=dict(l=0, r=0, t=10, b=0), template="plotly_white")
            st.plotly_chart(fig_disp, use_container_width=True)

else:
    st.info("👈 Por favor, carga tu archivo Excel (.xlsx) en la barra lateral para desplegar los controles operativos.")
