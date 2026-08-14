"""
App/CuentaEspeciales/config.py

Centraliza todas las rutas y constantes del bot.
Si cambia algo estructural, se cambia acá y no hay que tocar bot.py.
"""

import os
 
# ── Rutas base ────────────────────────────────────────────────────────────────
BASE_DIR    = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))   # Carpeta raíz del proyecto BABOT (dos niveles arriba de este archivo)
DESKTOP     = os.path.join(os.path.expanduser("~"), "Desktop")                       # Carpeta del Desktop del usuario actual
IMAGES_DIR  = os.path.join(os.path.dirname(__file__), "images")                      # Carpeta de imágenes de referencia para reconocimiento visual
SETTINGS_PATH = os.path.join(BASE_DIR, "Config", "settings.xlsx")                    # Excel de configuración general (usuario, contraseña, etc.)
OUTPUTS_DIR = os.path.join(BASE_DIR, "data", "Outputs")                # Carpeta de outputs donde se guardan los Excels descargados
INPUTS_DIR  = os.path.join(BASE_DIR, "data", "Inputs")                               # Carpeta de inputs    


# ── Ejecutable del sistema Major ──────────────────────────────────────────────
MAJOR_DIR   = r"\\mpilar2\Major\CBProgramas\Rafam\Rentas53.exe"
MAJOR_PROC  = "Rentas53.exe"
TOOLKIT_PROC = "Toolkit.exe"


# ── Configuración del Excel de entrada ───────────────────────────────────────
# Variables del Bot principal
ROW_USUARIO    = 2
ROW_CONTRASENA = 3
ROW_HOJA_EXCEL = 5
ROW_NOMBRE_EXCEL = 4

# Variables para la api
ROW_API_DOMINO = 5
ROW_API_TOKEN_URL = 6
ROW_API_USUARIO = 7
ROW_API_CONTRASENIA = 8


# ── Timeouts (segundos) ───────────────────────────────────────────────────────
TIMEOUT_LOGIN       = 15    # espera para que aparezca la pantalla de login
TIMEOUT_VENTANA     = 360   # espera máxima para que aparezca un elemento
TIMEOUT_TABLA       = 120   # espera para que cargue la tabla de deudas
TIMEOUT_GUARDAR     = 240   # espera para el diálogo guardar archivo


# ── Confianza mínima para reconocimiento de imágenes ─────────────────────────
# pyautogui usa un valor entre 0 y 1 (el locators.json usa 0-100)
CONFIDENCE = 0.7
