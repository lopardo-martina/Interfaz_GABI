"""
App/CuentaEspeciales/funcionesAuxiliares/unificar_excel.py
 
Convierte los archivos .xls descargados por el bot principal y los unifica
en un único Excel con columnas estandarizadas y clasificación de deuda.
 
Orden de ejecución: 1° dentro del post-proceso.
"""

import os
import pandas as pd
from datetime import datetime, timedelta
from io import StringIO


HOY = datetime.now()
LIMITE_5_ANIOS = HOY - timedelta(days=5*365)

# Encabezados nuevos
NEW_HEADERS = [
    "tasa", "subtasa", "", "rubro", "", "periodo", "cuota", "importe", 
    "accesorios", "total", "", "vencimiento", "recargo", "condicion", "cuenta", "periodo_calculado", "deuda_al" 
]

def clasificar(fecha):
    if pd.isna(fecha):
        return "sin_clasificacion"
    elif fecha > HOY:
        return "no_vencida"
    elif fecha < LIMITE_5_ANIOS:
        return "no_exigible"
    else:
        return "exigible"    
    

def agregar_clasificacion(ruta_unificado: str, log):
    """Agrega la columna 'clasificacion' al Excel unificado."""
    df = pd.read_excel(ruta_unificado)
    
    df["vencimiento"] = pd.to_datetime(df["vencimiento"], format="%d/%m/%Y", errors="coerce")
    
    df["clasificacion"] = df["vencimiento"].apply(clasificar)
    
    df.to_excel(ruta_unificado, index=False)
    
    log("Columna 'clasificacion' agregada", "ok")
    
    
    
    

def convertir_y_unificar_archivos(outputs_dir: str, log=None):
    """
    Lee todos los .xls de la carpeta Deudas_tss, los unifica en un solo Excel
    y agrega la columna de clasificación.
 
    Args:
        outputs_dir: ruta base de outputs (data/outputs/)
        log: función de logging — recibe (mensaje, tipo)
    """
    
    # carpeta de entrada: deudas_tss
    input_folder = os.path.join(outputs_dir, "Deudas_tss")
    
    #Carpeta de salida: outputs/año-tss/mes/dia
    fecha_hoy = datetime.now()
    output_folder = os.path.join(
        outputs_dir,
        f"{fecha_hoy.strftime('%Y')}-tss",
        fecha_hoy.strftime("%m"),
        fecha_hoy.strftime("%d"),
    )
    os.makedirs(output_folder, exist_ok=True)
 
    if not os.path.exists(input_folder):
        log(f"Carpeta de entrada no encontrada: {input_folder}", "error")
        return
    
    archivos_procesados = 0
    df_unificado = pd.DataFrame()


    for file_name in os.listdir(input_folder):
        if file_name.endswith('.xls'):
            input_path = os.path.join(input_folder, file_name)
            try:
                with open(input_path, 'r', encoding='latin1') as file:
                    html_content = file.read()
                
                tables = pd.read_html(StringIO(html_content))
                if not tables:
                    print(f"No se encontraron tablas en el archivo {file_name}.")
                    continue
                
                df = tables[0]
                df = df.iloc[1:].dropna(how='all')
                df.columns = NEW_HEADERS[:-2]
                cuenta_number = file_name.split('.')[0].zfill(20)
                df["cuenta"] = cuenta_number
                def calcular_periodo(row):
                    try:
                        periodo = int(row["periodo"])
                        mes = int(row["cuota"])
                        if 1900 <= periodo <= 2100 and 1 <= mes <= 12:
                            return f"{periodo}-{mes:02d}-01"
                    except (ValueError, TypeError):
                        return None
                
                print(df.columns.tolist())
                df["periodo_calculado"] = df.apply(calcular_periodo, axis=1)
                df["deuda_al"] = datetime.fromtimestamp(os.path.getmtime(input_path)).strftime("%Y-%m-%d")
                df_unificado = pd.concat([df_unificado, df], ignore_index=True)
                
                archivos_procesados += 1
                log(f"Archivo procesado: {file_name}", "info")
            except Exception as e:
                log(f"Error procesando {file_name}: {e}", "error")
    
    if not df_unificado.empty:
        output_unificado = os.path.join(output_folder, "unificado.xlsx")
        df_unificado.to_excel(output_unificado, index=False)
        log(f"Archivo unificado guardado en: {output_unificado}", "info")
        agregar_clasificacion(output_unificado, log)
        log("Agregada la columna Clasificacion", "info")
    else:
        log("No se procesaron archivos.", "warn")

    log(f"Total de archivos procesados: {archivos_procesados}", "info")
    


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__),"..", "..", "..")))
    from App.CuentaEspeciales.config import OUTPUTS_DIR
    
    convertir_y_unificar_archivos(OUTPUTS_DIR)

