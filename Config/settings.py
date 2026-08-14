"""
core/settings.py

Toda la interacción con config/settings.json pasa por acá.
Reemplaza al viejo core/excel_utils.py: los paneles y el runner importan
estas funciones y nunca tocan el JSON directamente.

Estructura del settings.json:
{
    "app":   { "nombre_bot": "GABI", "equipo": "" },
    "smtp":  { "user": "", "pass": "", "mail_destino": "", "notif_mail": false },
    "rutas": { "logs": "data/logs" },
    "bots":  [
        {
            "nombre": "DeudaDescargas",
            "ruta":   "App/deuda/main.py",
            "activo": true,
            "config": { }          # variables propias del bot (las edita el usuario)
        }
    ]
}

Separación de responsabilidades:
  - Constantes de sistema (host/puerto SMTP, rutas)  → core/config.py
  - Datos editables por el usuario                   → este JSON
  - Variables propias de cada bot                    → bloque "config" de cada bot
"""

import os
import json
import copy

from .config import SETTINGS_PATH, LOGS_DIR_DEFAULT


# ──────────────────────────────────────────────────────────────────────────
# Estructura por defecto — se usa si el archivo no existe o está corrupto
# ──────────────────────────────────────────────────────────────────────────

_DEFAULT = {
    "app":   {"nombre_bot": "GABI", "equipo": ""},
    "smtp":  {"user": "", "pass": "", "mail_destino": "", "notif_mail": False},
    "rutas": {"logs": LOGS_DIR_DEFAULT},
    "bots":  [],
}


# ──────────────────────────────────────────────────────────────────────────
# Lectura / escritura de bajo nivel
# ──────────────────────────────────────────────────────────────────────────

def _leer() -> dict:
    """
    Lee y parsea el settings.json completo.
    Si el archivo no existe o está mal formado, devuelve una copia de la
    estructura por defecto (nunca lanza excepción hacia arriba).
    """
    if not os.path.exists(SETTINGS_PATH):
        return copy.deepcopy(_DEFAULT)
    try:
        with open(SETTINGS_PATH, encoding="utf-8") as f:
            data = json.load(f)
        # Garantizamos que estén todas las secciones esperadas
        for seccion, valor in _DEFAULT.items():
            data.setdefault(seccion, copy.deepcopy(valor))
        return data
    except (json.JSONDecodeError, OSError) as e:
        print(f"[settings] Error leyendo {SETTINGS_PATH}: {e}")
        return copy.deepcopy(_DEFAULT)


def _escribir(data: dict) -> bool:
    """
    Escribe el dict completo al settings.json (con indentación legible).
    Devuelve True si guardó bien, False si hubo error.
    Crea la carpeta config/ si no existe.
    """
    try:
        os.makedirs(os.path.dirname(SETTINGS_PATH), exist_ok=True)
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except OSError as e:
        print(f"[settings] Error guardando {SETTINGS_PATH}: {e}")
        return False


# ──────────────────────────────────────────────────────────────────────────
# Bots — lista de robots a ejecutar
# ──────────────────────────────────────────────────────────────────────────

def leer_bots() -> list[dict]:
    """
    Devuelve la lista de bots:
    [
        {"nombre": "DeudaDescargas", "ruta": "App/...", "activo": True, "config": {}},
        ...
    ]
    Devuelve lista vacía si no hay bots.
    """
    bots = _leer().get("bots", [])
    # Normalizamos: garantizamos que cada bot tenga todas las claves
    for b in bots:
        b.setdefault("nombre", "")
        b.setdefault("ruta", "")
        b.setdefault("activo", False)
        b.setdefault("config", {})
    return bots


def guardar_bots(bots: list[dict]) -> bool:
    """
    Sobreescribe la lista de bots, preservando el resto del JSON
    (config global, smtp, rutas).
    Devuelve True si guardó bien.
    """
    data = _leer()
    data["bots"] = bots
    return _escribir(data)


def agregar_bot(nombre: str, ruta: str) -> bool:
    """
    Agrega un bot nuevo al final de la lista.
    Su bloque 'config' arranca vacío: las variables propias del bot se
    agregan después a mano en el settings.json, y el usuario edita los
    valores desde el panel.
    """
    bots = leer_bots()
    bots.append({
        "nombre": nombre,
        "ruta":   ruta,
        "activo": False,
        "config": {},
    })
    return guardar_bots(bots)


def eliminar_bot(indice: int) -> bool:
    """Elimina el bot en la posición indicada (0-indexed)."""
    bots = leer_bots()
    if 0 <= indice < len(bots):
        bots.pop(indice)
        return guardar_bots(bots)
    return False


def config_de_bot(nombre: str) -> dict:
    """
    Devuelve el bloque 'config' del bot con ese nombre.
    Pensado para que cada bot lea SUS variables sin colisionar con otros:

        from core.settings import config_de_bot
        cfg = config_de_bot("DeudaDescargas")
        url = cfg.get("url", "")

    Devuelve dict vacío si el bot no existe o no tiene config.
    """
    for b in leer_bots():
        if b["nombre"] == nombre:
            return b.get("config", {})
    return {}


def guardar_config_de_bot(nombre: str, config: dict) -> bool:
    """
    Actualiza el bloque 'config' de un bot puntual (deja el resto intacto).
    Lo usa el panel cuando el usuario edita las variables de un bot.
    """
    bots = leer_bots()
    for b in bots:
        if b["nombre"] == nombre:
            b["config"] = config
            return guardar_bots(bots)
    return False


# ──────────────────────────────────────────────────────────────────────────
# Configuración global — app / smtp / rutas
# ──────────────────────────────────────────────────────────────────────────

def leer_config_global() -> dict:
    """
    Devuelve las secciones editables de config global como un solo dict:
    {
        "app":   {...},
        "smtp":  {...},
        "rutas": {...},
    }
    """
    data = _leer()
    return {
        "app":   data.get("app", {}),
        "smtp":  data.get("smtp", {}),
        "rutas": data.get("rutas", {}),
    }


def guardar_config_global(config: dict) -> bool:
    """
    Guarda las secciones de config global recibidas, preservando la lista
    de bots. Espera un dict con las claves 'app', 'smtp', 'rutas'.
    """
    data = _leer()
    for seccion in ("app", "smtp", "rutas"):
        if seccion in config:
            data[seccion] = config[seccion]
    return _escribir(data)


# ──────────────────────────────────────────────────────────────────────────
# Accesos rápidos usados por notificador / runner
# ──────────────────────────────────────────────────────────────────────────

def ruta_logs() -> str:
    """Ruta de la carpeta de logs (o el default si no está configurada)."""
    return _leer().get("rutas", {}).get("logs") or LOGS_DIR_DEFAULT


def smtp_config() -> dict:
    """Credenciales SMTP editables (user, pass, mail_destino, notif_mail)."""
    return _leer().get("smtp", {})


def nombre_equipo() -> str:
    """Nombre del equipo configurado por el usuario (puede venir vacío)."""
    return _leer().get("app", {}).get("equipo", "")


def nombre_bot_sistema() -> str:
    """Nombre que GABI usa en los reportes (default 'GABI')."""
    return _leer().get("app", {}).get("nombre_bot") or "GABI"