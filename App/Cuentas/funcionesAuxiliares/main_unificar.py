"""
App/CuentaEspeciales/funcionesAuxiliares/main.py

Punto de entrada del post-proceso de CuentaEspeciales.
Registrá este archivo en BABOT como un bot separado.

Orden de ejecución:
    1. unificar_excel  → convierte .xls y genera unificado.xlsx
    2. limpiar_excel   → limpia cta_tss.xlsx y mueve archivos

Puede correrse:
    - Desde BABOT (runner lo llama con subprocess)
    - Directo: python App/CuentaEspeciales/funcionesAuxiliares/main.py
"""

import sys
import os
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from App.CuentaEspeciales.config import INPUTS_DIR, OUTPUTS_DIR, SETTINGS_PATH
from App.CuentaEspeciales.funcionesAuxiliares.unificar import convertir_y_unificar_archivos
from App.CuentaEspeciales.funcionesAuxiliares.limpieza_input import limpiar_excel


# Logger simple que usa prefijos reconocidos por el runner de BABOT
def log(mensaje: str, tipo: str = ""):
    prefijos = {
        "info":  "INFO: ",
        "ok":    "| PASS | ",
        "warn":  "WARNING: ",
        "error": "| FAIL | ",
        "dim":   "",
    }
    print(f"{prefijos.get(tipo, '')}{mensaje}", flush=True)


def main():
    log("=" * 50, "dim")
    log("Iniciando post-proceso CuentaEspeciales", "info")
    log("=" * 50, "dim")

    # 1. Enviar datos nuevos a la API
    log("─── Paso 1: Enviar datos a API ───", "info")
    try:
        convertir_y_unificar_archivos(OUTPUTS_DIR, log)
    except Exception as e:
        log(f"Error en convertir_y_unificar_archivos: {e}", "error")
        sys.exit(1)

    # 2. Limpiar Excel
    log("─── Paso 2: Limpiar Excel ───", "info")
    try:
        limpiar_excel(INPUTS_DIR, OUTPUTS_DIR, log)
    except Exception as e:
        log(f"Error en limpiar_excel: {e}", "error")
        sys.exit(1)

    log("=" * 50, "dim")
    log("Post-proceso finalizado correctamente", "ok")
    log("=" * 50, "dim")
    sys.exit(0)


if __name__ == "__main__":
    main()