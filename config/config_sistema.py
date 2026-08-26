"""
core/config_sistema.py

Constantes de sistema de GABI.

Acá viven los valores que definen CÓMO funciona GABI y que un usuario final
no debería tocar nunca: son parte de la lógica, no datos operativos. Si cambian,
los cambia el desarrollador y hace un commit.

La configuración editable por el usuario (credenciales, destinatarios,
ruta de logs, variables de cada bot) vive en config/settings.json y se maneja
desde config/almacenamiento.py.
"""

import os

# ──────────────────────────────────────────────────────────────────────────
# Rutas base
# ──────────────────────────────────────────────────────────────────────────

# Raíz del proyecto (carpeta que contiene a core/, ui/, config/, ...).
# __file__ está en core/config.py, así que subimos un nivel.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Archivo de configuración editable.
SETTINGS_PATH = os.path.join(BASE_DIR, "config", "settings.json")

# Carpeta de logs por defecto, si el usuario no configuró otra en el JSON.
LOGS_DIR_DEFAULT = os.path.join("data", "logs")


# ──────────────────────────────────────────────────────────────────────────
# SMTP — parámetros de sistema
# ──────────────────────────────────────────────────────────────────────────
# El host y el puerto son fijos del proveedor de correo (gmail acá).
# Las credenciales y destinatarios NO van acá: son del usuario y viven en el
# JSON para no hardcodear datos sensibles en el código versionado.

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
