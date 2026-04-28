# GABI — Gestion Automatizada Bots de Ingresos

<table border="none; border-collapse: collapse;">
<tr>
<td width="70%" style="border: none;">

Gestor de bots RPA de escritorio construido en Python. Permite ejecutar, configurar y monitorear bots de automatización que interactúan con el Sistema Major.

</td>
<td width="30%" align="center" style="border: none;">

<img src="Statics/logo-day.png" alt="GABI Logo" width="180"/>

</td>
</tr>
</table>

---

## Características

- Interfaz dark moderna con CustomTkinter
- Ejecución de múltiples bots en secuencia con log en tiempo real
- Activación/desactivación de bots por toggle sin tocar código
- Editor de configuración integrado (settings.xlsx)
- Reconocimiento de imágenes con OpenCV para interacción con UI legacy

---

## Estructura del proyecto

```
GABI/
├── main.py                          # Punto de entrada de la interfaz
├── dev_runner.py                    # Auto-reload para desarrollo
├── check_bot.py                     # Verificación pre-ejecución
├── extract_images.py                # Extrae imágenes del locators.json
├── requirements.txt
│
├── core/
│   ├── runner.py                    # Ejecuta bots via subprocess, captura output
│   └── excel_utils.py               # Leer/escribir settings.xlsx
│
├── ui/
│   ├── main_window.py               # Ventana principal + sidebar + navegación
│   └── panels/
│       ├── panel_main.py            # Log de ejecución + botones Iniciar/Detener
│       ├── panel_bots.py            # Gestión de bots registrados
│       └── panel_config.py          # Editor de configuración
│
├── App/
│   └── BotEjemplo/
│       ├── main.py                  # Punto de entrada del bot
│       ├── bot.py                   # Lógica completa
│       ├── config.py                # Rutas y constantes
│       ├── images/                  # Imágenes de referencia para reconocimiento visual
│       └── funcionesAuxiliares/
│           ├── main.py              # Orquestador del post-proceso
│           └── funcionEjemplo.py    # Funciones/procesos que se requieren luego del bot
│
├── config/
│   └── settings.xlsx                # Configuración general (NO incluir en repo)
│
├── data/
│   ├── inputs/                      # Excels de entrada para los bots
│   ├── outputs/                     # Archivos generados por los bots
│   └── logs/                        # Logs de ejecución diarios
│
└── statics/                         # Íconos y recursos visuales
```

---

## Configuración (settings.xlsx)

El archivo `config/settings.xlsx` tiene dos hojas:

**Sheet1 — configuración general**

| Fila | CLAVE | VALOR | DETALLE |
|------|-------|-------|-------|
| 2 | USUARIO_MAJOR | PEPITO | usuario de acceso al sistema Major |
| 3 | PASSWORD_MAJOR | PEPITO123 | contraseña del sistema Major |
| 6 | MI_EXCEL | Excel.xlsx | nombre del archivo Excel a utilizar |
| 7 | HOJA_EXCEL | Sheet1 | nombre de la hoja del Excel |

**robots — lista de bots registrados**

| Nombre Script | Dato | Valor |
|---------------|------|-------|
| BotEjemplo | App/BotEjemplo/main.py | SI |
| FuncionEjemplo | App/BotEjemplo/funcionesAuxiliares/main.py | NO |

`Valor = SI` activa el bot. `Valor = NO` lo desactiva sin eliminarlo.

---

## Agregar un nuevo bot

1. Crear la carpeta `App/NombreBot/` con esta estructura:

```
App/NombreBot/
├── main.py       # punto de entrada — registrar este archivo en BABOT
├── bot.py        # clase con la lógica
├── config.py     # rutas y constantes
└── images/       # imágenes de referencia para reconocimiento visual
```

2. El `main.py` debe seguir este patrón:

```python
import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from App.NombreBot.bot import BotNombre

def log(mensaje, tipo=""):
    prefijos = {"info": "INFO: ", "ok": "| PASS | ", "warn": "WARNING: ", "error": "| FAIL | ", "dim": ""}
    print(f"{prefijos.get(tipo, '')}{mensaje}", flush=True)

if __name__ == "__main__":
    try:
        bot = BotNombre(logger=log)
        bot.ejecutar()
        sys.exit(0)
    except InterruptedError as e:
        log(str(e), "warn")
        sys.exit(0)
    except Exception as e:
        log(f"Error fatal: {e}", "error")
        sys.exit(1)
```

3. Registrar el bot en BABOT desde el panel **Scripts/Bots → Agregar bot**, seleccionando el `main.py`.

---

## Dependencias principales

| Paquete | Uso |
|---------|-----|
| customtkinter | Interfaz de usuario moderna |
| openpyxl / pandas | Leer y escribir Excel |
| pyautogui | Control de mouse y teclado |
| opencv-python | Reconocimiento de imágenes |
| pygetwindow | Detección de ventanas por título |
| pywinauto | Interacción con controles de Windows por ID |
| psutil | Gestión de procesos |
| pyperclip | Copiar rutas al portapapeles |
| requests | Llamadas a la API REST |
| watchdog | Auto-reload en desarrollo |
| pyinstaller | Empaquetado como .exe |
