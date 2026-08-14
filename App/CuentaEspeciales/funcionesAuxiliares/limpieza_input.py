"""
App/CuentaEspeciales/funcionesAuxiliares/limpiar_excel.py
 
Elimina las columnas B, C y D del Excel de cuentas (cta_tss.xlsx)
y mueve los archivos de Deudas_tss a la carpeta con fecha estructurada.
 
Orden de ejecución: 2° dentro del post-proceso.
"""

import os
import shutil
import pandas as pd
from datetime import datetime

# Configuración de rutas
desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
inputs_path = os.path.join(desktop_path, "BABOT_deuda_inmueble", "Inputs")
outputs_path = os.path.join(desktop_path, "BABOT_deuda_inmueble", "Outputs")
deudas_path = os.path.join(desktop_path, "BABOT_deuda_inmueble", "Outputs", "Deudas_tss")
ruta_archivo = os.path.join(inputs_path, "cta_tss.xlsx")

def mover_archivos_a_carpeta_fecha(origen: str, outputs_dir: str, log):
    """
    Mueve los archivos de la carpeta origen a:
    outputs_dir/YYYY-tss/MM/DD/Deudas_tss/
    """
    
    fecha       = datetime.now()
    ruta_destino = os.path.join(
        outputs_dir,
        f"{fecha.strftime('%Y')}-tss",
        fecha.strftime("%m"),
        fecha.strftime("%d"),
        "Deudas_tss",
    )
    os.makedirs(ruta_destino, exist_ok=True)
 
    movidos = 0

    # Mover los archivos de la carpeta origen a la carpeta destino
    for archivo in os.listdir(origen):
        archivo_origen = os.path.join(origen, archivo)
        if os.path.isfile(archivo_origen):
            shutil.move(archivo_origen, ruta_destino)
            
            log(f"Movido: {archivo} → {ruta_destino}", "dim")
            movidos += 1

    log(f"{movidos} archivos movidos a {ruta_destino}", "ok")



def limpiar_excel(inputs_dir: str, outputs_dir: str, log=None):
    """
    Elimina columnas B, C y D de cta_tss.xlsx y mueve los archivos de Deudas_tss.
 
    Args:
        inputs_dir:  ruta a data/inputs/
        outputs_dir: ruta a data/outputs/
        log:         función de logging — recibe (mensaje, tipo)
    """
    if log is None:
        log = lambda msg, tipo="": print(f"[{tipo.upper() or 'INFO'}] {msg}", flush=True)
    
    ruta_archivo  = os.path.join(inputs_dir, "cta_tss.xlsx")
    deudas_path   = os.path.join(outputs_dir, "Deudas_tss")
    
    # ── Limpiar columnas del Excel de cuentas ─────────────────────────────────
    if not os.path.exists(ruta_archivo):
        log(f"Archivo no encontrado: {ruta_archivo}", "error")
        return
 
    try:
        df = pd.read_excel(ruta_archivo, header=None)
        total_cols = df.shape[1]
 
        # Columnas B=1, C=2, D=3 (índice 0-based)
        cols_a_eliminar = [col for col in [1, 2, 3] if col < total_cols]
 
        if cols_a_eliminar:
            df.drop(columns=cols_a_eliminar, inplace=True)
            log(f"Columnas eliminadas: {[chr(66 + i) for i in range(len(cols_a_eliminar))]}", "info")
        else:
            log("No hay columnas B/C/D para eliminar", "dim")
 
        df.to_excel(ruta_archivo, index=False, header=False)
        log(f"Excel limpiado: {ruta_archivo}", "ok")
 
    except Exception as e:
        log(f"Error limpiando Excel: {e}", "error")
        return
 
    # ── Mover archivos de Deudas_tss ─────────────────────────────────────────
    if os.path.exists(deudas_path):
            mover_archivos_a_carpeta_fecha(deudas_path, outputs_dir, log)
    else:
        log(f"Carpeta Deudas_tss no encontrada: {deudas_path}", "warn")



if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
    from App.CuentaEspeciales.config import INPUTS_DIR, OUTPUTS_DIR
    limpiar_excel(INPUTS_DIR, OUTPUTS_DIR)
