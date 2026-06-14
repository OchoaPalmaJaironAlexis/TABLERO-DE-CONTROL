import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Tablero HACCP - Recepción", layout="wide")
st.title("🦐 Panel de Liberación de Lotes y Control de Calidad")

# --- CARGA DE DATOS ---
st.sidebar.header("📂 Carga de Datos")
archivo = st.sidebar.file_uploader("Sube el archivo HACCP", type=["xlsx"])

if archivo:
    df = pd.read_excel(archivo)
    
    # Filtro Temporal
    meses = ["Todos"] + sorted(list(df['Mes'].unique()))
    mes_sel = st.sidebar.selectbox("Filtro por Mes:", meses)
    if mes_sel != "Todos":
        df = df[df['Mes'] == mes_sel]

    # =========================================================================
    # 0. TARJETAS KPI (CABECERA)
    # =========================================================================
    st.markdown("### 📌 Indicadores Críticos del Periodo")
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    
    # KPI 1: Tasa de Aprobación
    total_lotes = len(df)
    aprobados = len(df[df['Estado_Lote'] == 'APROBADO'])
    tasa_aprobacion = (aprobados / total_lotes) * 100 if total_lotes > 0 else 0
    kpi1.metric("Tasa de Aprobación", f"{tasa_aprobacion:.1f}%", f"{aprobados} de {total_lotes} Lotes")

    # KPI 2: Top Proveedor Crítico
    rechazados_retenidos = df[df['Estado_Lote'].isin(['RECHAZADO', 'RETENIDO'])]
    if not rechazados_retenidos.empty:
        top_proveedor = rechazados_retenidos['Proveedor'].value_counts().idxmax()
        kpi2.metric("⚠️ Proveedor con Más Alertas", top_proveedor)
    else:
        kpi2.metric("⚠️ Proveedor con Más Alertas", "Sin Alertas")

    # KPI 3 & 4: Semáforos de Límites Cero Tolerancia
    melanosis_detectada = df['DM_Melanosis'].max() > 0
    temp_critica = df['Temperatura_Arribo'].max() > 4.0
    
    if melanosis_detectada:
        kpi3.error("🔴 ALERTA: Melanosis Detectada (>0%)")
    else:
        kpi3.success("🟢 Melanosis: 0% (Conforme)")
        
    if temp_critica:
        kpi4.error(f"🔴 ALERTA Temp: Max {df['Temperatura_Arribo'].max():.1f}°C")
    else:
        kpi4.success("🟢 Temp Arribo: < 4.0°C (Conforme)")

    st.divider()

    # =========================================================================
    # 1. VARIABLES CRÍTICAS DE CONTROL
    # =========================================================================
    st.markdown("### 1️⃣ Variables Críticas de Control (Inocuidad)")
    col1_1, col1_2 = st.columns(2)

    with col1_1:
        # Gráfico de Línea: Temperatura
        fig_temp = px.line(df, x='Lote', y='Temperatura_Arribo', markers=True, color='Proveedor', title="Temperatura de Arribo por Lote (Límite: 4°C)")
        fig_temp.add_hrect(y0=0, y1=4, fillcolor="green", opacity=0.1, line_width=0)
        fig_temp.add_hline(y=4, line_dash="dash", line_color="red", annotation_text="Límite Máximo 4°C")
        st.plotly_chart(fig_temp, use_container_width=True)

    with col1_2:
        # Gráfico SPC: Sulfito Residual
        fig_sulf = px.scatter(df, x='Lote', y='Sulfito_Residual', color='Proveedor', title="Control de Sulfito Residual (Límite: 100 ppm)")
        fig_sulf.add_hline(y=df['Sulfito_Residual'].mean(), line_color="blue", annotation_text="Media")
        fig_sulf.add_hline(y=100, line_dash="dash", line_color="red", annotation_text="Límite Legal (100 ppm)")
        st.plotly_chart(fig_sulf, use_container_width=True)

    st.divider()

    # =========================================================================
    # 2. VARIABLES DE PESO Y UNIFORMIDAD
    # =========================================================================
    st.markdown("### 2️⃣ Control de Peso, Talla y Uniformidad")
    col2_1, col2_2 = st.columns([2, 1])

    with col2_1:
        # Gráfico de Barras Agrupadas: Pesos Drenados
        # Transformar datos para graficar las 3 muestras
        df_pesos = df[['Lote', 'Peso_Guia', 'Peso_M1', 'Peso_M2', 'Peso_M3']].melt(id_vars=['Lote', 'Peso_Guia'], var_name='Muestra', value_name='Peso (g)')
        fig_peso = px.bar(df_pesos, x='Lote', y='Peso (g)', color='Muestra', barmode='group', title="Pesos Drenados vs Peso Declarado")
        fig_peso.add_trace(go.Scatter(x=df['Lote'], y=df['Peso_Guia'], mode='lines', name='Peso Guía Ideal', line=dict(color='black', width=3, dash='dot')))
        st.plotly_chart(fig_peso, use_container_width=True)

    with col2_2:
        # Tacómetro de Uniformidad (Promedio del mes)
        uniformidad_prom = df['Uniformidad'].mean()
        fig_uni = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = uniformidad_prom,
            title = {'text': "Factor de Uniformidad Promedio"},
            gauge = {
                'axis': {'range': [1.0, 1.8]},
                'bar': {'color': "black"},
                'steps': [
                    {'range': [1.0, 1.4], 'color': "lightgreen"},
                    {'range': [1.4, 1.8], 'color': "salmon"}
                ],
                'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': 1.4}
            }
        ))
        st.plotly_chart(fig_uni, use_container_width=True)

    st.divider()

    # =========================================================================
    # 3. CONTROL DE DEFECTOS (MAYORES Y MENORES)
    # =========================================================================
    st.markdown("### 3️⃣ Composición de Defectos y Tendencias")
    col3_1, col3_2 = st.columns(2)

    # Nombres de las columnas de defectos
    defectos_cols = ['DM_Melanosis', 'DM_Deshidratacion', 'DM_Cabeza_Negra', 'DM_Cabeza_Roja', 'DM_Cabeza_Floja', 'DM_Estropeado',
                     'DMen_Antenas_Rotas', 'DMen_Cola_Rota', 'DMen_Blando', 'DMen_Manchas', 'DMen_Mudado', 'DMen_Vena']

    with col3_1:
        # Diagrama de Pareto de los 12 Defectos
        suma_defectos = df[defectos_cols].sum().sort_values(ascending=False)
        df_pareto = pd.DataFrame({'Defecto': suma_defectos.index, 'Impacto': suma_defectos.values})
        df_pareto['Acumulado %'] = (df_pareto['Impacto'].cumsum() / df_pareto['Impacto'].sum()) * 100

        fig_pareto = make_subplots(specs=[[{"secondary_y": True}]])
        fig_pareto.add_trace(go.Bar(x=df_pareto['Defecto'], y=df_pareto['Impacto'], marker_color='#34495e', name="Total Detectado"), secondary_y=False)
        fig_pareto.add_trace(go.Scatter(x=df_pareto['Defecto'], y=df_pareto['Acumulado %'], mode='lines+markers', line=dict(color='#e74c3c', width=3), name="% Acumulado"), secondary_y=True)
        fig_pareto.update_layout(title="Pareto: Impacto Acumulado de los 12 Defectos", showlegend=False)
        st.plotly_chart(fig_pareto, use_container_width=True)

    with col3_2:
        # Tendencia de Defectos Mayores vs Menores
        fig_tendencia = go.Figure()
        fig_tendencia.add_trace(go.Scatter(x=df['Lote'], y=df['Total_Defectos_Mayores'], mode='lines', name='Total Mayores', line=dict(color='darkred')))
        fig_tendencia.add_trace(go.Scatter(x=df['Lote'], y=df['Total_Defectos_Menores'], mode='lines', name='Total Menores', line=dict(color='orange')))
        
        # Líneas de Límite Legal
        fig_tendencia.add_hline(y=12, line_dash="dash", line_color="darkred", annotation_text="Límite Mayores (12%)")
        fig_tendencia.add_hline(y=15, line_dash="dash", line_color="orange", annotation_text="Límite Menores (15%)")
        
        fig_tendencia.update_layout(title="Tendencia Histórica: Límites de Calidad Permitidos")
        st.plotly_chart(fig_tendencia, use_container_width=True)

else:
    st.info("Sube el archivo 'datos_haccp_camaron.xlsx' en el menú lateral para inicializar el sistema.")
