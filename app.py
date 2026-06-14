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
    
    # Agrupación
    opciones_agrupacion = [col for col in ['Lote', 'Día', 'Semana', 'Mes'] if col in df.columns]
    agrupacion = st.sidebar.selectbox("Agrupar gráficos por:", opciones_agrupacion if opciones_agrupacion else df.columns[0])
    
    st.sidebar.header("🔬 3. Selección de Variables")
    variables_sel = st.sidebar.multiselect("Variables a analizar:", cols_numericas, default=cols_numericas[:1])

    st.sidebar.header("🛠️ 4. Herramientas Visuales")
    t_barras = st.sidebar.checkbox("Composición de Defectos (Barras)", value=True)
    t_pareto = st.sidebar.checkbox("Diagrama de Pareto (80/20)", value=True)
    t_control = st.sidebar.checkbox("Gráfico de Control (SPC)", value=True)
    t_dispersion = st.sidebar.checkbox("Diagrama de Dispersión (Regresión)", value=True)

    # --- MOTOR LÓGICO Y RENDERIZADO ---
    if not variables_sel:
        st.warning("⚠️ Selecciona al menos una variable en la barra lateral para generar los gráficos.")
    else:
        # APLICAR FILTROS
        df_filtro = df.copy()
        if mes_seleccionado != "Todo el Histórico":
            df_filtro = df_filtro[df_filtro['Mes'] == mes_seleccionado]
            
        if df_filtro.empty:
            st.error("No hay datos para el mes seleccionado.")
            st.stop()

        # APLICAR AGRUPACIÓN
        if agrupacion == 'Lote' or agrupacion not in df_filtro.columns:
            df_plot = df_filtro.copy()
            eje_x = agrupacion if agrupacion in df_filtro.columns else df_filtro.index
        else:
            df_plot = df_filtro.groupby(agrupacion)[variables_sel].mean().reset_index()
            df_plot[agrupacion] = df_plot[agrupacion].astype(str)
            eje_x = agrupacion

        var_principal = variables_sel[0]

        # --- SECCIÓN SUPERIOR: KPIs (TACÓMETROS NATIVOS) ---
        st.markdown("### 📌 Indicadores Clave (Promedios del Periodo)")
        cols_kpi = st.columns(min(len(variables_sel), 4))
        for i, var in enumerate(variables_sel[:4]):
            media_actual = df_plot[var].mean()
            cols_kpi[i].metric(label=var, value=f"{media_actual:.2f}")

        st.divider()

        # --- SECCIÓN CENTRAL: GRÁFICOS ---
        col1, col2 = st.columns(2)

        # 1. BARRAS APILADAS
        if t_barras:
            with col1:
                st.subheader("📊 Composición de Variables")
                fig_bar = px.bar(df_plot, x=eje_x, y=variables_sel, color_discrete_sequence=px.colors.qualitative.Pastel)
                fig_bar.update_layout(height=400, barmode='stack', margin=dict(l=0, r=0, t=30, b=0))
                st.plotly_chart(fig_bar, use_container_width=True)

        # 2. DIAGRAMA DE PARETO
        if t_pareto:
            with col2:
                st.subheader("📈 Diagrama de Pareto")
                promedios = {var: df_filtro[var].mean() for var in variables_sel}
                df_p = pd.DataFrame(list(promedios.items()), columns=['Var', 'Val']).sort_values(by='Val', ascending=False)
                if df_p['Val'].sum() > 0:
                    df_p['Cum'] = (df_p['Val'].cumsum() / df_p['Val'].sum()) * 100
                    fig_p = make_subplots(specs=[[{"secondary_y": True}]])
                    fig_p.add_trace(go.Bar(x=df_p['Var'], y=df_p['Val'], name="Impacto", marker_color='#2c3e50'), secondary_y=False)
                    fig_p.add_trace(go.Scatter(x=df_p['Var'], y=df_p['Cum'], name="% Acum", mode='lines+markers', line=dict(color='#e74c3c', width=3)), secondary_y=True)
                    fig_p.update_layout(height=400, margin=dict(l=0, r=0, t=30, b=0))
                    fig_p.update_yaxes(range=[0, 105], secondary_y=True)
                    st.plotly_chart(fig_p, use_container_width=True)

        # 3. GRÁFICO DE CONTROL SPC
        if t_control:
            st.divider()
            st.subheader(f"🎯 Gráfico de Control SPC: {var_principal}")
            fig_spc = go.Figure()
            y_data = df_plot[var_principal]
            media, desv = y_data.mean(), y_data.std()
            
            fig_spc.add_trace(go.Scatter(x=df_plot[eje_x], y=y_data, mode='lines+markers', name='Datos', line=dict(color='#2980b9')))
            if not np.isnan(media) and not np.isnan(desv):
                fig_spc.add_hline(y=media, line_color="green", annotation_text="Media Global")
                fig_spc.add_hline(y=media + 3*desv, line_color="red", line_dash="dash", annotation_text="LSC (+3σ)")
                fig_spc.add_hline(y=max(0, media - 3*desv), line_color="red", line_dash="dash", annotation_text="LIC (-3σ)")
            
            fig_spc.update_layout(height=400, margin=dict(l=0, r=0, t=30, b=0))
            st.plotly_chart(fig_spc, use_container_width=True)

        # 4. DIAGRAMA DE DISPERSIÓN (CON DIAGNÓSTICO MATEMÁTICO)
        if t_dispersion:
            st.divider()
            st.subheader("🔍 Análisis de Correlación (Diagrama de Dispersión)")
            if len(variables_sel) >= 2:
                var1, var2 = variables_sel[0], variables_sel[1]
                
                # Calcular correlación de Pearson
                mask = np.isfinite(df_filtro[var1]) & np.isfinite(df_filtro[var2])
                r_pearson = 0
                diagnostico = "Datos insuficientes"
                
                if mask.sum() > 2:
                    r_pearson, _ = stats.pearsonr(df_filtro[var1][mask], df_filtro[var2][mask])
                    if r_pearson > 0.7: diagnostico = "Correlación Positiva Evidente ↗️"
                    elif r_pearson > 0.3: diagnostico = "Correlación Positiva ↗️"
                    elif r_pearson > -0.3: diagnostico = "Sin Correlación 🔀"
                    elif r_pearson > -0.7: diagnostico = "Correlación Negativa ↘️"
                    else: diagnostico = "Correlación Negativa Evidente ↘️"

                # Mostrar Diagnóstico en pantalla
                col_diag1, col_diag2 = st.columns(2)
                col_diag1.info(f"**Diagnóstico del Patrón:** {diagnostico}")
                col_diag2.info(f"**Coeficiente de Pearson (r):** {r_pearson:.3f}")

                # Determinar color de los puntos (por Agrupación si es posible)
                color_col = agrupacion if agrupacion in df_filtro.columns else None
                
                fig_disp = px.scatter(df_filtro, x=var1, y=var2, color=color_col, trendline="ols",
                                      color_continuous_scale='Viridis')
                
                # Estilo: Nube de puntos semi-transparente y línea de tendencia roja sólida
                fig_disp.update_traces(marker=dict(size=9, opacity=0.7), selector=dict(mode='markers'))
                fig_disp.update_traces(line=dict(color='red', width=4), selector=dict(mode='lines'))
                fig_disp.update_layout(height=500, margin=dict(l=0, r=0, t=10, b=0))
                
                st.plotly_chart(fig_disp, use_container_width=True)
            else:
                st.warning("⚠️ Selecciona exactamente 2 variables en el menú lateral para evaluar su correlación.")

else:
    st.info("👈 Esperando datos... Por favor, carga tu archivo Excel (.xlsx) en la barra lateral para iniciar.")
