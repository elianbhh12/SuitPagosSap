
import pandas as pd
import numpy as np
from io import BytesIO
import logging
from typing import Tuple, List, Optional, Union
from pathlib import Path


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SAPDataProcessor:

    
    def __init__(self, data_path: str = "."):

        self.data_path = Path(data_path)
        self.ventas_df = None
        self.pagos_df = None
        self.stock_df = None
        
    def cargar_datos(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:

        archivos = {
            'ventas': 'F_ventas_sap.xlsx',
            'pagos': 'F_pagos_clientes.xlsx',
            'stock': 'MM_stock_actual.xlsx'
        }
        
        try:
            logger.info("Iniciando carga de datos...")
            
            # Verificar que los archivos existen
            for nombre, archivo in archivos.items():
                ruta_archivo = self.data_path / archivo
                if not ruta_archivo.exists():
                    raise FileNotFoundError(f"No se encontró el archivo: {archivo}")
            
            # Cargar datos
            self.ventas_df = pd.read_excel(self.data_path / archivos['ventas'])
            self.pagos_df = pd.read_excel(self.data_path / archivos['pagos'])
            self.stock_df = pd.read_excel(self.data_path / archivos['stock'])
            
            # Validar estructura de datos
            self._validar_estructura_datos()
            
            # Limpiar datos
            self._limpiar_datos()
            
            logger.info("Datos cargados exitosamente")
            return self.ventas_df, self.pagos_df, self.stock_df
            
        except FileNotFoundError as e:
            logger.error(f"Error de archivo: {e}")
            raise
        except Exception as e:
            logger.error(f"Error al cargar datos: {e}")
            raise Exception(f"Error al cargar los archivos: {str(e)}")
    
    def _validar_estructura_datos(self) -> None:
        """Valida que los DataFrames tengan las columnas necesarias"""
        columnas_requeridas = {
            'ventas': ['Doc_Venta', 'Fecha_Doc', 'Cliente', 'Nombre_Cliente', 'Canal', 'Producto', 'Cantidad', 'Valor_Neto', 'Moneda'],
            'pagos': ['Doc_Pago', 'Fecha_Pago', 'Cliente', 'Nombre_Cliente', 'Banco', 'Monto_Pago', 'Moneda', 'Referencia_Factura'],
            'stock': ['Material', 'Descripción', 'Centro', 'Tipo_Almacén', 'Stock_Total', 'Unidad_Medida']
        }
        
        datasets = {
            'ventas': self.ventas_df,
            'pagos': self.pagos_df,
            'stock': self.stock_df
        }
        
        for nombre, df in datasets.items():
            columnas_faltantes = set(columnas_requeridas[nombre]) - set(df.columns)
            if columnas_faltantes:
                raise ValueError(f"Columnas faltantes en {nombre}: {columnas_faltantes}")
    
    def _limpiar_datos(self) -> None:
        """Limpia y prepara los datos para su procesamiento"""
        # Limpiar datos de ventas
        self.ventas_df = self.ventas_df.dropna(subset=['Doc_Venta'])
        self.ventas_df['Cantidad'] = pd.to_numeric(self.ventas_df['Cantidad'], errors='coerce').fillna(0)
        self.ventas_df['Valor_Neto'] = pd.to_numeric(self.ventas_df['Valor_Neto'], errors='coerce').fillna(0)
        
        # Convertir fechas de ventas
        if 'Fecha_Doc' in self.ventas_df.columns:
            self.ventas_df['Fecha_Doc'] = pd.to_datetime(self.ventas_df['Fecha_Doc'], errors='coerce')
        
        # Limpiar datos de pagos
        self.pagos_df = self.pagos_df.dropna(subset=['Referencia_Factura'])
        self.pagos_df['Monto_Pago'] = pd.to_numeric(self.pagos_df['Monto_Pago'], errors='coerce').fillna(0)
        
        # Convertir fechas de pagos
        if 'Fecha_Pago' in self.pagos_df.columns:
            self.pagos_df['Fecha_Pago'] = pd.to_datetime(self.pagos_df['Fecha_Pago'], errors='coerce')
        
        # Limpiar datos de stock
        self.stock_df['Stock_Total'] = pd.to_numeric(self.stock_df['Stock_Total'], errors='coerce').fillna(0)
    
    def aplicar_filtros(self, 
                       df: pd.DataFrame,
                       productos: Optional[List[str]] = None,
                       clientes: Optional[List[str]] = None,
                       moneda: Optional[str] = None) -> pd.DataFrame:

        df_filtrado = df.copy()
        
        try:
            if productos:
                df_filtrado = df_filtrado[df_filtrado['Producto'].isin(productos)]
                logger.info(f"Filtro aplicado: {len(productos)} productos seleccionados")
            
            if clientes:
                df_filtrado = df_filtrado[df_filtrado['Nombre_Cliente'].isin(clientes)]
                logger.info(f"Filtro aplicado: {len(clientes)} clientes seleccionados")
            
            if moneda and moneda != "Todas":
                df_filtrado = df_filtrado[df_filtrado['Moneda'] == moneda]
                logger.info(f"Filtro aplicado: moneda {moneda}")
            
            logger.info(f"Registros después del filtro: {len(df_filtrado)}")
            return df_filtrado
            
        except Exception as e:
            logger.error(f"Error al aplicar filtros: {e}")
            return df
    
    def calcular_kpis(self, ventas_df: pd.DataFrame, pagos_df: pd.DataFrame) -> Tuple[float, float, float]:

        try:
            # Calcular total de ventas
            total_ventas = (ventas_df['Cantidad'] * ventas_df['Valor_Neto']).sum()
            
            # Calcular total pagado (solo para las ventas filtradas)
            docs_ventas = ventas_df['Doc_Venta'].unique()
            pagos_filtrados = pagos_df[pagos_df['Referencia_Factura'].isin(docs_ventas)]
            total_pagado = pagos_filtrados['Monto_Pago'].sum()
            
            # Calcular pendiente
            pendiente_cobrar = total_ventas - total_pagado
            
            logger.info(f"KPIs calculados - Ventas: {total_ventas:,.2f}, Pagado: {total_pagado:,.2f}, Pendiente: {pendiente_cobrar:,.2f}")
            
            return total_ventas, total_pagado, pendiente_cobrar
            
        except Exception as e:
            logger.error(f"Error al calcular KPIs: {e}")
            return 0.0, 0.0, 0.0


    def generar_reporte_excel(self, 
                                ventas_df: pd.DataFrame,
                                pagos_df: pd.DataFrame,
                                stock_df: pd.DataFrame,
                                incluir_resumen: bool = True) -> bytes:

            try:
                output = BytesIO()
                
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    # Configurar formatos
                    workbook = writer.book
                    
                    # Formato para encabezados
                    header_format = workbook.add_format({
                        'bold': True,
                        'text_wrap': True,
                        'valign': 'top',
                        'fg_color': '#D7E4BC',
                        'border': 1
                    })
                    
                    # Formato para números
                    number_format = workbook.add_format({'num_format': '#,##0.00'})
                    
                    # Escribir hojas
                    ventas_df.to_excel(writer, sheet_name='Ventas', index=False)
                    pagos_df.to_excel(writer, sheet_name='Pagos', index=False)
                    stock_df.to_excel(writer, sheet_name='Stock', index=False)
                    
                    # Aplicar formato a las hojas
                    datasets = {
                        'Ventas': ventas_df,
                        'Pagos': pagos_df,
                        'Stock': stock_df
                    }
                    
                    for sheet_name, df in datasets.items():
                        worksheet = writer.sheets[sheet_name]
                        
                        # Aplicar formato a encabezados
                        for col_num, column_name in enumerate(df.columns):
                            worksheet.write(0, col_num, column_name, header_format)
                        
                        # Ajustar ancho de columnas
                        worksheet.set_column(0, len(df.columns), 15)
                        
                        # Aplicar formato numérico a columnas numéricas
                        for col_num, column_name in enumerate(df.columns):
                            if df[column_name].dtype in ['int64', 'float64']:
                                worksheet.set_column(col_num, col_num, 15, number_format)
                    
                    # Hoja de resumen si se solicita
                    if incluir_resumen:
                        self._crear_hoja_resumen(writer, ventas_df, pagos_df, stock_df)
                
                output.seek(0)
                logger.info("Reporte Excel generado exitosamente")
                return output.getvalue()
                
            except Exception as e:
                logger.error(f"Error al generar reporte Excel: {e}")
                raise Exception(f"Error al generar el reporte: {str(e)}")
    
    def _crear_hoja_resumen(self, writer, ventas_df, pagos_df, stock_df):
        """Crea una hoja de resumen con KPIs y estadísticas"""
        total_ventas, total_pagado, pendiente = self.calcular_kpis(ventas_df, pagos_df)
        
        resumen_data = {
            'Métrica': [
                'Total Ventas',
                'Total Pagado',
                'Pendiente por Cobrar',
                'Productos Únicos',
                'Clientes Únicos',
                'Transacciones de Venta',
                'Transacciones de Pago',
                'Materiales en Stock',
                'Centros de Distribución',
                'Stock Total (Unidades)'
            ],
            'Valor': [
                total_ventas,
                total_pagado,
                pendiente,
                len(ventas_df['Producto'].unique()) if not ventas_df.empty else 0,
                len(ventas_df['Nombre_Cliente'].unique()) if not ventas_df.empty else 0,
                len(ventas_df),
                len(pagos_df),
                len(stock_df[stock_df['Stock_Total'] > 0]) if not stock_df.empty else 0,
                len(stock_df['Centro'].unique()) if not stock_df.empty else 0,
                stock_df['Stock_Total'].sum() if not stock_df.empty else 0
            ]
        }
        
        resumen_df = pd.DataFrame(resumen_data)
        resumen_df.to_excel(writer, sheet_name='Resumen', index=False)
        
        # Aplicar formato a la hoja de resumen
        worksheet = writer.sheets['Resumen']
        workbook = writer.book
        
        # Formato para encabezados
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'top',
            'fg_color': '#D7E4BC',
            'border': 1
        })
        
        # Formato para números
        number_format = workbook.add_format({'num_format': '#,##0.00'})
        
        # Aplicar formato a encabezados
        for col_num, column_name in enumerate(resumen_df.columns):
            worksheet.write(0, col_num, column_name, header_format)
        
        # Ajustar ancho de columnas
        worksheet.set_column(0, 0, 30)  # Columna de métricas más ancha
        worksheet.set_column(1, 1, 20, number_format)  # Columna de valores con formato numérico



def cargar_datos():
    processor = SAPDataProcessor()
    return processor.cargar_datos()

def filtro_avanzado(df, productos, clientes, moneda):
    processor = SAPDataProcessor()
    return processor.aplicar_filtros(df, productos, clientes, moneda)

def generar_kpis(ventas_df, pagos_df):
    processor = SAPDataProcessor()
    return processor.calcular_kpis(ventas_df, pagos_df)

def generar_excel(df1, df2, df3):
    processor = SAPDataProcessor()
    return processor.generar_reporte_excel(df1, df2, df3)