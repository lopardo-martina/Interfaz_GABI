"""
Toda la interacción con el archivo settings.xlsx pasa por acá.
Los paneles importan estas funciones y nunca tocan openpyxl directamente.

Estructura esperada del Excel:
  - Hoja "Sheet1": configuración general (URL, usuario, contraseña, etc.)
    Columnas: CLAVE | VALOR
  - Hoja "robots": lista de bots
    Columnas: Nombre Script | Dato (ruta) | Valor (SI/NO)
"""

import os
import openpyxl
import pandas as pd
from openpyxl import load_workbook

EXCEL_PATH = os.path.join("config", "settings.xlsx")


# Hoja "robots" — lista de bots

def leer_bots() -> list[dict]:
    """
    Lee la hoja 'robots' y devuelve una lista de dicts:
    [
        {"nombre": "DeudaDescargas", "ruta": "bots/...", "activo": True},
        ...
    ]
    Devuelve lista vacía si el archivo o la hoja no existen.
    """
    if not os.path.exists(EXCEL_PATH):
        return []
    try:
        wb = load_workbook(EXCEL_PATH)
        if "robots" not in wb.sheetnames:
            return []
        hoja = wb["robots"]
        bots = []
        for row in hoja.iter_rows(min_row=2, values_only=True):
            nombre, ruta, valor = row[0], row[1], row[2]
            if nombre or ruta:   # ignorar filas completamente vacías
                bots.append({
                    "nombre": nombre or "",
                    "ruta":   ruta   or "",
                    "activo": str(valor).upper() == "SI",
                })
        return bots
    except Exception as e:
        print(f"[excel_utils] Error leyendo bots: {e}")
        return []


def guardar_bots(bots: list[dict]) -> bool:
    """
    Sobreescribe la hoja 'robots' con la lista recibida.
    Devuelve True si guardó bien, False si hubo error.
    """
    if not os.path.exists(EXCEL_PATH):
        return False
    try:
        wb = load_workbook(EXCEL_PATH)

        # Si la hoja no existe la creamos; si existe la limpiamos
        if "robots" not in wb.sheetnames:
            wb.create_sheet("robots")
        hoja = wb["robots"]

        # Limpiar contenido anterior (excepto fila 1 con encabezados)
        for row in hoja.iter_rows(min_row=2):
            for cell in row:
                cell.value = None

        # Escribir encabezados si la hoja estaba vacía
        hoja["A1"] = "Nombre Script"
        hoja["B1"] = "Dato"
        hoja["C1"] = "Valor"

        # Escribir cada bot
        for i, bot in enumerate(bots, start=2):
            hoja.cell(row=i, column=1, value=bot["nombre"])
            hoja.cell(row=i, column=2, value=bot["ruta"])
            hoja.cell(row=i, column=3, value="SI" if bot["activo"] else "NO")

        wb.save(EXCEL_PATH)
        return True
    except Exception as e:
        print(f"[excel_utils] Error guardando bots: {e}")
        return False


def agregar_bot(nombre: str, ruta: str) -> bool:
    """Agrega un bot nuevo al final de la hoja 'robots'."""
    bots = leer_bots()
    bots.append({"nombre": nombre, "ruta": ruta, "activo": False})
    return guardar_bots(bots)


def eliminar_bot(indice: int) -> bool:
    """Elimina el bot en la posición indicada (0-indexed)."""
    bots = leer_bots()
    if 0 <= indice < len(bots):
        bots.pop(indice)
        return guardar_bots(bots)
    return False




# Hoja "Sheet1" — configuración general

def leer_config() -> list[dict]:
    """
    Lee la hoja 'Sheet1' y devuelve lista de dicts:
    [
        {"clave": "URL", "valor": "https://...", "detalle": "Portal principal"},
        ...
    ]
    Solo devuelve filas que tengan al menos clave o valor.
    """
    if not os.path.exists(EXCEL_PATH):
        return []
    try:
        wb = load_workbook(EXCEL_PATH)
        hoja = wb["Sheet1"]
        config = []
        for row in hoja.iter_rows(min_row=2, values_only=True):
            # Esperamos columnas: CLAVE | VALOR | DETALLES (opcional)
            clave   = row[0] if len(row) > 0 else None
            valor   = row[1] if len(row) > 1 else None
            detalle = row[2] if len(row) > 2 else None
            if clave or valor:
                config.append({
                    "clave":   str(clave)   if clave   is not None else "",
                    "valor":   str(valor)   if valor   is not None else "",
                    "detalle": str(detalle) if detalle is not None else "",
                })
        return config
    except Exception as e:
        print(f"[excel_utils] Error leyendo config: {e}")
        return []


def guardar_config(config: list[dict]) -> bool:
    """
    Sobreescribe la hoja 'Sheet1' con la configuración recibida.
    Preserva los encabezados originales.
    Devuelve True si guardó bien.
    """
    if not os.path.exists(EXCEL_PATH):
        return False
    try:
        wb = load_workbook(EXCEL_PATH)
        hoja = wb["Sheet1"]

        # Limpiar filas de datos (desde fila 2)
        for row in hoja.iter_rows(min_row=2):
            for cell in row:
                cell.value = None

        # Escribir datos actualizados
        for i, item in enumerate(config, start=2):
            hoja.cell(row=i, column=1, value=item["clave"])
            hoja.cell(row=i, column=2, value=item["valor"])
            hoja.cell(row=i, column=3, value=item["detalle"])

        wb.save(EXCEL_PATH)
        return True
    except Exception as e:
        print(f"[excel_utils] Error guardando config: {e}")
        return False