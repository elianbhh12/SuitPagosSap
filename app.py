import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import logging
from procesos import SAPDataProcessor

# Configuración de página
st.set_page_config(
    page_title="SAVI Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SAPDashboard:
   
    def __init__(self):
        self.processor = SAPDataProcessor()
        self.inicializar_session_state()
    
    def inicializar_session_state(self):
        if 'datos_cargados' not in st.session_state:
            st.session_state.datos_cargados = False
        if 'ventas_df' not in st.session_state:
            st.session_state.ventas_df = None
        if 'pagos_df' not in st.session_state:
            st.session_state.pagos_df = None
        if 'stock_df' not in st.session_state:
            st.session_state.stock_df = None
    
    def cargar_datos_iniciales(self):
        try:
            with st.spinner("Cargando datos..."):
                ventas, pagos, stock = self.processor.cargar_datos()
                st.session_state.ventas_df = ventas
                st.session_state.pagos_df = pagos
                st.session_state.stock_df = stock
                st.session_state.datos_cargados = True
                st.success(" Datos cargados exitosamente")
                st.rerun()
                
        except FileNotFoundError as e:
            st.error(f" Error: No se encontraron los archivos necesarios. {str(e)}")
            st.info(" Asegúrate de que los siguientes archivos estén en el directorio:")
            st.code("""
            • F_ventas_sap.xlsx
            • F_pagos_clientes.xlsx
            • MM_stock_actual.xlsx
            """)
        except Exception as e:
            st.error(f" Error al cargar datos: {str(e)}")
            logger.error(f"Error en carga de datos: {e}")
    
    def crear_sidebar(self):
        with st.sidebar:
            st.header(" Panel de Control")
            
            # Botón para recargar datos
            if st.button("Recargar Datos", use_container_width=True):
                st.session_state.datos_cargados = False
                st.rerun()
            
            if not st.session_state.datos_cargados:
                return None, None, None
            
            st.subheader(" Filtros de Análisis")
            
            # Filtros
            ventas_df = st.session_state.ventas_df
            
            productos = st.multiselect(
                " Productos",
                options=sorted(ventas_df['Producto'].unique()),
                default=None,
                help="Selecciona uno o más productos para filtrar"
            )
            
            clientes = st.multiselect(
                " Clientes",
                options=sorted(ventas_df['Nombre_Cliente'].unique()),
                default=None,
                help="Selecciona uno o más clientes para filtrar"
            )
            
            canales = st.multiselect(
                " Canales",
                options=sorted(ventas_df['Canal'].unique()),
                default=None,
                help="Selecciona uno o más canales de venta"
            )
            
            monedas_disponibles = ["Todas"] + sorted(ventas_df['Moneda'].unique().tolist())
            moneda = st.selectbox(
                " Moneda",
                options=monedas_disponibles,
                index=0,
                help="Selecciona la moneda para el análisis"
            )
            
            # Filtro de fechas
            st.subheader(" Filtros de Fecha")
            fecha_desde = st.date_input(
                "Desde",
                value=None,
                help="Fecha de inicio (opcional)"
            )
            fecha_hasta = st.date_input(
                "Hasta", 
                value=None,
                help="Fecha de fin (opcional)"
            )
            
            # Información de filtros aplicados
            st.subheader(" Filtros Activos")
            if productos:
                st.write(f"• **Productos**: {len(productos)} seleccionados")
            if clientes:
                st.write(f"• **Clientes**: {len(clientes)} seleccionados")
            if canales:
                st.write(f"• **Canales**: {len(canales)} seleccionados")
            if moneda != "Todas":
                st.write(f"• **Moneda**: {moneda}")
            if fecha_desde:
                st.write(f"• **Desde**: {fecha_desde}")
            if fecha_hasta:
                st.write(f"• **Hasta**: {fecha_hasta}")
            
            return productos, clientes, canales, moneda, fecha_desde, fecha_hasta
    
    def mostrar_kpis(self, ventas_filtradas, pagos_df):
        st.subheader(" Indicadores Clave de Rendimiento")
        
        # Calcular KPIs
        total_ventas, total_pagado, pendiente = self.processor.calcular_kpis(
            ventas_filtradas, pagos_df
        )
        
        # Mostrar métricas
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                " Ventas Totales",
                f"${total_ventas:,.0f}",
                delta=None,
                help="Total de ventas según los filtros aplicados"
            )
        
        with col2:
            st.metric(
                " Pagos Recibidos",
                f"${total_pagado:,.0f}",
                delta=None,
                help="Total de pagos recibidos"
            )
        
        with col3:
            st.metric(
                " Pendiente por Cobrar",
                f"${pendiente:,.0f}",
                delta=None,
                help="Diferencia entre ventas y pagos recibidos"
            )
        
        with col4:
            porcentaje_cobrado = (total_pagado / total_ventas * 100) if total_ventas > 0 else 0
            st.metric(
                " % Cobrado",
                f"{porcentaje_cobrado:.1f}%",
                delta=None,
                help="Porcentaje de ventas cobrado"
            )
        
        return total_ventas, total_pagado, pendiente
    
    def aplicar_filtros_completos(self, ventas_df, productos, clientes, canales, moneda, fecha_desde, fecha_hasta):
        df_filtrado = ventas_df.copy()
        
        try:
            # Filtros básicos
            df_filtrado = self.processor.aplicar_filtros(df_filtrado, productos, clientes, moneda)
            
            # Filtro por canal
            if canales:
                df_filtrado = df_filtrado[df_filtrado['Canal'].isin(canales)]
                logger.info(f"Filtro aplicado: {len(canales)} canales seleccionados")
            
            # Filtros de fecha
            if fecha_desde:
                df_filtrado = df_filtrado[df_filtrado['Fecha_Doc'] >= pd.to_datetime(fecha_desde)]
                logger.info(f"Filtro aplicado: fecha desde {fecha_desde}")
            
            if fecha_hasta:
                df_filtrado = df_filtrado[df_filtrado['Fecha_Doc'] <= pd.to_datetime(fecha_hasta)]
                logger.info(f"Filtro aplicado: fecha hasta {fecha_hasta}")
            
            return df_filtrado
            
        except Exception as e:
            logger.error(f"Error al aplicar filtros: {e}")
            return ventas_df
    def crear_graficos(self, ventas_filtradas, pagos_df, stock_df):
        st.subheader(" Análisis Visual")
        
        # Primera fila de gráficos
        col1, col2 = st.columns(2)
        
        with col1:
            # Gráfico de ventas por producto
            if not ventas_filtradas.empty:
                ventas_por_producto = ventas_filtradas.groupby('Producto').agg({
                    'Cantidad': 'sum',
                    'Valor_Neto': lambda x: (ventas_filtradas.loc[x.index, 'Cantidad'] * x).sum()
                }).reset_index()
                
                fig_ventas = px.bar(
                    ventas_por_producto,
                    x='Producto',
                    y='Valor_Neto',
                    title=' Ventas por Producto',
                    labels={'Valor_Neto': 'Valor Total ($)', 'Producto': 'Producto'}
                )
                fig_ventas.update_layout(showlegend=False)
                st.plotly_chart(fig_ventas, use_container_width=True)
            else:
                st.info("No hay datos de ventas para mostrar")
        
        with col2:
            # Gráfico de ventas por canal
            if not ventas_filtradas.empty:
                ventas_por_canal = ventas_filtradas.groupby('Canal').agg({
                    'Valor_Neto': lambda x: (ventas_filtradas.loc[x.index, 'Cantidad'] * x).sum()
                }).reset_index()
                
                fig_canal = px.pie(
                    ventas_por_canal,
                    values='Valor_Neto',
                    names='Canal',
                    title=' Distribución por Canal'
                )
                st.plotly_chart(fig_canal, use_container_width=True)
            else:
                st.info("No hay datos de canal para mostrar")
        
        # Segunda fila de gráficos
        col3, col4 = st.columns(2)
        
        with col3:
            # Gráfico de estado de stock
            if not stock_df.empty:
                stock_status = stock_df.copy()
                stock_status['Estado'] = stock_status['Stock_Total'].apply(
                    lambda x: 'Sin Stock' if x <= 0 else 'Stock Bajo' if x <= 50 else 'Stock Normal'
                )
                
                stock_counts = stock_status['Estado'].value_counts()
                
                fig_stock = px.pie(
                    values=stock_counts.values,
                    names=stock_counts.index,
                    title=' Estado del Stock',
                    color_discrete_map={
                        'Sin Stock': '#ff4444',
                        'Stock Bajo': '#ffaa00',
                        'Stock Normal': '#00aa00'
                    }
                )
                st.plotly_chart(fig_stock, use_container_width=True)
            else:
                st.info("No hay datos de stock para mostrar")
        
        with col4:
            # Gráfico de pagos por mes (si hay fechas)
            if not pagos_df.empty and 'Fecha_Pago' in pagos_df.columns:
                pagos_mensual = pagos_df.copy()
                pagos_mensual['Mes'] = pagos_mensual['Fecha_Pago'].dt.to_period('M')
                pagos_por_mes = pagos_mensual.groupby('Mes')['Monto_Pago'].sum().reset_index()
                pagos_por_mes['Mes'] = pagos_por_mes['Mes'].astype(str)
                
                fig_pagos = px.line(
                    pagos_por_mes,
                    x='Mes',
                    y='Monto_Pago',
                    title=' Evolución de Pagos',
                    markers=True
                )
                st.plotly_chart(fig_pagos, use_container_width=True)
            else:
                st.info("No hay datos de pagos temporales para mostrar")
    
    def mostrar_tablas_datos(self, ventas_filtradas, pagos_df, stock_df):
        st.subheader(" Datos Detallados")
        
        # Pestañas para organizar los datos
        tab1, tab2, tab3 = st.tabs([" Ventas", " Pagos", " Stock"])
        
        with tab1:
            st.write("**Ventas Detalladas**")
            if not ventas_filtradas.empty:
                # Agregar información de resumen
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Registros", len(ventas_filtradas))
                with col2:
                    st.metric("Productos Únicos", len(ventas_filtradas['Producto'].unique()))
                with col3:
                    st.metric("Clientes Únicos", len(ventas_filtradas['Nombre_Cliente'].unique()))
                
                st.dataframe(
                    ventas_filtradas,
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("No hay datos de ventas que coincidan con los filtros")
        
        with tab2:
            st.write("**Pagos Recibidos**")
            if not pagos_df.empty:
                st.metric("Total Pagos", len(pagos_df))
                st.dataframe(
                    pagos_df,
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("No hay datos de pagos disponibles")
        
        with tab3:
            st.write("**Inventario Actual**")
            if not stock_df.empty:
                # Métricas de stock
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Materiales en Stock", len(stock_df[stock_df['Stock_Total'] > 0]))
                with col2:
                    st.metric("Materiales Agotados", len(stock_df[stock_df['Stock_Total'] <= 0]))
                with col3:
                    st.metric("Stock Total", f"{stock_df['Stock_Total'].sum():,.0f}")
                
                # Mostrar información adicional
                st.write(f"**Centros de Distribución**: {len(stock_df['Centro'].unique())}")
                st.write(f"**Tipos de Almacén**: {len(stock_df['Tipo_Almacén'].unique())}")
                
                st.dataframe(
                    stock_df,
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("No hay datos de stock disponibles")
    
    def generar_reporte(self, ventas_filtradas, pagos_df, stock_df):
        st.subheader("Descargar Reporte")
        
        col1, col2 = st.columns(2)
        
        with col1:
            incluir_resumen = st.checkbox("Incluir hoja de resumen", value=True)
            incluir_graficos = st.checkbox("Incluir datos para gráficos", value=False)
        
        with col2:
            if st.button("Generar Reporte", use_container_width=True):
                try:
                    with st.spinner("Generando reporte..."):
                        excel_data = self.processor.generar_reporte_excel(
                            ventas_filtradas,
                            pagos_df,
                            stock_df,
                            incluir_resumen=incluir_resumen
                        )
                    
                    # Generar nombre de archivo con timestamp
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"Reporte_SAP_{timestamp}.xlsx"
                    
                    st.download_button(
                        label="📥 Descargar Reporte Consolidado",
                        data=excel_data,
                        file_name=filename,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                    
                    st.success(" Reporte generado exitosamente")
                    
                    
                except Exception as e:
                    st.error(f" Error al generar reporte: {str(e)}")
                    logger.error(f"Error en generación de reporte: {e}")
    
    def ejecutar(self):

        st.title(" Dashboard SAP Simulado")
        st.markdown("---")
        st.markdown("###  Análisis de Ventas, Pagos y Stock")
        
        # Cargar datos si no están cargados
        if not st.session_state.datos_cargados:
            self.cargar_datos_iniciales()
            return
        

        filtros = self.crear_sidebar()
        
        if filtros[0] is None:  # Si no se pudo crear el sidebar
            return
            
        productos, clientes, canales, moneda, fecha_desde, fecha_hasta = filtros
        
        # Aplicar filtros
        ventas_filtradas = self.aplicar_filtros_completos(
            st.session_state.ventas_df,
            productos,
            clientes,
            canales,
            moneda,
            fecha_desde,
            fecha_hasta
        )
        
        # Mostrar KPIs
        total_ventas, total_pagado, pendiente = self.mostrar_kpis(
            ventas_filtradas,
            st.session_state.pagos_df
        )
        
        st.markdown("---")
        
        # Crear gráficos
        self.crear_graficos(
            ventas_filtradas,
            st.session_state.pagos_df,
            st.session_state.stock_df
        )
        
        st.markdown("---")
        
        # Mostrar tablas de datos
        self.mostrar_tablas_datos(
            ventas_filtradas,
            st.session_state.pagos_df,
            st.session_state.stock_df
        )
        
        st.markdown("---")
        

        self.generar_reporte(
            ventas_filtradas,
            st.session_state.pagos_df,
            st.session_state.stock_df
        )
        

        st.markdown("---")
        st.markdown("*© 2025 Elian Dev. Hecho con Streamlit*")


if __name__ == "__main__":
    dashboard = SAPDashboard()
    dashboard.ejecutar()
