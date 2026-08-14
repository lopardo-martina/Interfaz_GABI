"""
App/CuentaEspeciales/funcionesAuxiliares/main.py

Punto de entrada del post-proceso de CuentaEspeciales.
Registrá este archivo en BABOT como un bot separado.

Orden de ejecución:
    1. eliminar_deudas → elimina deudas viejas en la API
    2. enviar_api      → sube el unificado.xlsx a la API

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
from App.CuentaEspeciales.funcionesAuxiliares.api_eliminar import eliminar_deudas
from App.CuentaEspeciales.funcionesAuxiliares.api import enviar_datos_a_api


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

    # 1. Eliminar deudas viejas
    log("─── Paso 1: Eliminar deudas viejas ───", "info")
    try:
        eliminar_deudas(INPUTS_DIR, SETTINGS_PATH, log)
    except Exception as e:
        log(f"Error en eliminar_deudas: {e}", "error")
        sys.exit(1)

    # 2. Enviar datos nuevos a la API
    log("─── Paso 2: Enviar datos a API ───", "info")
    try:
        enviar_datos_a_api(OUTPUTS_DIR, SETTINGS_PATH, log)
    except Exception as e:
        log(f"Error en enviar_datos_a_api: {e}", "error")
        sys.exit(1)

    log("=" * 50, "dim")
    log("Post-proceso finalizado correctamente", "ok")
    log("=" * 50, "dim")
    sys.exit(0)


if __name__ == "__main__":
    main()