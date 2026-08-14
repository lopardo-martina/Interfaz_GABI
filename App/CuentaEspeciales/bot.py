"""
App/CuentaEspeciales/bot.py

Migración completa del tasks.robot a Python puro.

Dependencias:
    pip install pyautogui pygetwindow openpyxl pandas psutil pillow

Estructura del bot (espeja los Keywords del .robot original):
    1. crear_carpetas()     → verifica/crea Outputs/Deudas
    2. abrir_major()        → abre Rentas53.exe y hace login
    3. recorrer_deudas()    → itera el Excel y descarga cada deuda

El bot recibe un logger (función) para enviar mensajes al log de BABOT.
Si no se pasa logger, imprime en consola (útil para testing manual).
"""

import os
import time
import subprocess
import psutil
import pyautogui
import numpy as np
import cv2
import pygetwindow as gw
import openpyxl
from openpyxl import load_workbook

from App.CuentaEspeciales.config import (
    MAJOR_DIR, MAJOR_PROC, TOOLKIT_PROC,
    SETTINGS_PATH, OUTPUTS_DIR, INPUTS_DIR, IMAGES_DIR,
    ROW_USUARIO, ROW_CONTRASENA, ROW_HOJA_EXCEL, ROW_NOMBRE_EXCEL,
    ROW_API_USUARIO, ROW_API_CONTRASENIA,
    TIMEOUT_VENTANA, TIMEOUT_TABLA, TIMEOUT_GUARDAR,
    CONFIDENCE,
)

from core.bot_base import BotBase

# pyautogui: no pausar entre acciones por defecto (lo manejamos con sleep explícito)
pyautogui.PAUSE = 0.1
# Deshabilitar el failsafe solo si estás seguro; lo dejamos en True por seguridad
pyautogui.FAILSAFE = True


class BotCuentasEspeciales(BotBase):
    """
    Encapsula toda la lógica del bot.
    """

    def __init__(self, logger=None, stop_event=None):
        super().__init__(logger, stop_event)
        self.IMAGES_DIR = IMAGES_DIR   
        self.CONFIDENCE = CONFIDENCE 

    # ──────────────────────────────────────────────────────────────────────────
    # Punto de entrada principal
    # ──────────────────────────────────────────────────────────────────────────

    def ejecutar(self):
        """Ejecuta el flujo completo del bot."""
        self.log("Iniciando bot CuentasEspeciales", "info")
        self.crear_carpetas()
        self._check_stop()
        self.abrir_major()
        self._check_stop()
        self.recorrer_deudas()
        self.log("Bot finalizado correctamente", "ok")





    # ──────────────────────────────────────────────────────────────────────────
    # 1. Creación de carpetas
    # ──────────────────────────────────────────────────────────────────────────

    def crear_carpetas(self):
        """Verifica y crea la carpeta de outputs si no existe."""
        output_dir = os.path.join(OUTPUTS_DIR, "Deudas")
        self.log(f"Verificando carpeta de outputs: {OUTPUTS_DIR} y {output_dir}", "info")

        if not os.path.exists(OUTPUTS_DIR):
            os.makedirs(OUTPUTS_DIR)
            self.log(f"Carpeta creada: {OUTPUTS_DIR}", "ok")
        else:
            self.log("Carpeta de outputs ya existe", "dim")
            
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            self.log(f"Carpeta creada: {output_dir}", "ok")
        else:
            self.log("Carpeta de outputs ya existe", "dim")





    # ──────────────────────────────────────────────────────────────────────────
    # 2. Abrir Major y hacer login
    # ──────────────────────────────────────────────────────────────────────────

    def abrir_major(self):
        """
        Abre Rentas53.exe (Major) y hace login.
        Si ya está abierto, lo cierra primero para evitar estados inconsistentes.
        Equivale al keyword 'Abrir Major' del .robot original.
 
        El login NO usa imágenes — usa pygetwindow para encontrar la ventana
        por título (igual que RPA.Windows.Click "Ingreso al Sistema" en el .robot)
        y Tab para navegar entre campos (equivalente a id:2).
        """
        usuario, contrasena = self._leer_credenciales()
        self.log(f"Usuario: {usuario}", "info")
 
        # Si ya está corriendo, cerrarlo limpiamente
        if self._proceso_existe(MAJOR_PROC):
            self.log("Major ya estaba abierto, reiniciando...", "warn")
            self._matar_proceso(TOOLKIT_PROC)
            self._matar_proceso(MAJOR_PROC)
            time.sleep(3)
  
        # Abrir Major
        # Abrir Major igual que Win+R — misma forma que usaba el bot anterior con robocorp
        self.log(f"Abriendo Major", "info")
        pyautogui.hotkey("win", "r")
        time.sleep(1)
        pyautogui.typewrite(MAJOR_DIR, interval=0.05)
        pyautogui.press("enter")
        time.sleep(5)
 
        # Esperar la ventana de login buscándola por título
        # Equivale a: RPA.Windows.Click "Ingreso al Sistema" timeout=120
        self.log("Esperando a iniciar sesión...", "info")
        ventana_login = self._esperar_ventana("Ingreso al Sistema", timeout=120)
        if not ventana_login:
            raise RuntimeError("No apareció la pantalla de login de Major")
 
        # Conectar con pywinauto para interactuar por ID de control
        # Equivale exactamente a: RPA.Windows.Click id:2 del .robot original
        try:
            from pywinauto import Application
            app = Application(backend="win32").connect(title_re=".*Ingreso al Sistema.*")
            win = app.window(title_re=".*Ingreso al Sistema.*")
            win.set_focus()
            time.sleep(0.5)
 
            # 1. Click en id:2 → campo usuario
            self.log("Ingresando usuario...", "info")
            campo_usuario = win.child_window(control_id=2)
            campo_usuario.click_input()
            time.sleep(0.3)
            campo_usuario.type_keys(str(usuario), with_spaces=True)
 
            # 2. Enter → pasa al campo contraseña
            pyautogui.press("enter")
            time.sleep(2)
 
            # 3. Escribir contraseña (el foco ya está en el campo)
            self.log("Ingresando contraseña...", "info")
            pyautogui.typewrite(str(contrasena), interval=0.05)
 
        except Exception as e:
            # Fallback con Tab si pywinauto no puede conectar
            self.log(f"pywinauto falló ({e}), usando Tab como fallback", "warn")
            try:
                ventana_login.activate()
            except Exception:
                pass
            time.sleep(0.5)
            pyautogui.press("tab")
            pyautogui.typewrite(str(usuario), interval=0.05)
            pyautogui.press("enter")
            time.sleep(2)
            pyautogui.typewrite(str(contrasena), interval=0.05)
 
        # 4. Enter → apunta al botón Aceptar
        # 5. Enter → presiona el botón Aceptar
        pyautogui.press("enter")
        time.sleep(0.5)
        pyautogui.press("enter")
 
        self.log("Login enviado, esperando pantalla principal...", "info")
        time.sleep(5)






    # ──────────────────────────────────────────────────────────────────────────
    # 3. Recorrer deudas
    # ──────────────────────────────────────────────────────────────────────────

    def recorrer_deudas(self):
        """
        Lee el Excel de cuentas e itera por cada fila descargando la deuda.
        Equivale al keyword 'RecorrerDeudas' del .robot original.
        """
        # Leer configuración del Excel
        nombre_excel, hoja_excel = self._leer_config_excel()
        ruta_excel = os.path.join(INPUTS_DIR, f"{nombre_excel}.xlsx")

        self.log(f"Leyendo Excel de cuentas: {ruta_excel}", "info")

        wb = load_workbook(ruta_excel)
        ws = wb[hoja_excel]

        # Preparar columnas de control (orden y estado)
        # Columna B = orden, Columna C = estado (OK / vacío)
        ws.cell(row=1, column=2, value="orden")
        ws.cell(row=1, column=3, value="excel")

        # Asignar número de orden a cada fila
        filas = list(ws.iter_rows(min_row=2, values_only=False))
        for i, fila in enumerate(filas, start=2):
            ws.cell(row=i, column=2, value=i)
        wb.save(ruta_excel)

        # Recargar filas con datos actualizados
        wb       = load_workbook(ruta_excel)
        ws       = wb[hoja_excel]
        filas    = list(ws.iter_rows(min_row=2, values_only=True))

        # Ingresar a Cuentas Especiales
        # Esperamos que aparezca el botón y hacemos click (mismo elemento)
        self.log("Navegando a Cuentas Especiales...", "info")
        if not self._esperar_imagen("cta_especiales", timeout=TIMEOUT_VENTANA):
            raise RuntimeError("No se encontró el menú de Cuentas Especiales")

        if not self._click_imagen("cta_especiales"):
            self.log("Falló el ingreso a Ctas. Especiales, reiniciando...", "warn")
            self._reiniciar()
            return

        self.log("Ingreso a Ctas. Especiales correcto", "ok")

        # Iterar por cada cuenta
        for fila in filas:
            self._check_stop()

            # Columnas del Excel: partida, orden, excel (estado)
            if len(fila) < 3:
                continue

            comercio = str(fila[0]) if fila[0] else ""
            orden = fila[1]
            estado = str(fila[2]) if fila[2] else ""

            if not comercio:
                continue

            # Si ya tiene OK, saltear
            if estado.upper() == "OK":
                self.log(f"Ya procesada: {comercio}", "dim")
                continue

            self.log(f"{'─'*50}", "dim")
            self.log(f"Procesando cuenta: {comercio}", "info")

            # Buscar la cuenta
            exito = self._buscar_cuenta(comercio)
            #self.log("se busco cuenta...", "info")
            if not exito:
                self.log("Falló al buscar la cuenta, reiniciando...", "warn")
                self._marcar_fila(ruta_excel, hoja_excel, orden, "OK", "NO SE ENCONTRO LA DEUDA")
                #self._reiniciar()
                continue
            time.sleep(2)
            
            # Abrir informe de deuda
            self.log("Abriendo informe de deuda...", "info")
            boton_deuda = self._esperar_imagen("deudas_especiales", timeout=TIMEOUT_TABLA)
            if not boton_deuda:
                self.log("No se encontró el botón de deudas especiales", "error")
                continue
            self._click_imagen("deudas_especiales")
            time.sleep(5)

            # Esperar tabla
            tabla_cargada = self._esperar_imagen("Tabla_Ingresos", timeout=TIMEOUT_TABLA)
            time.sleep(5)

            if not tabla_cargada:
                self.log("Error cargando tabla, reiniciando...", "error")
                self._reiniciar()
                return

            # La tabla está vacía?
            if self._imagen_existe("TablaVacia"):
                self.log(f"Sin deuda: {comercio}", "ok")
                self._matar_proceso(TOOLKIT_PROC)
                self._marcar_fila(ruta_excel, hoja_excel, orden, "OK", "SIN DEUDA")
                continue

            # Exportar a Excel
            self.log(f"Exportando deuda de: {comercio}", "info")
            self._exportar_excel(comercio)

            self._matar_proceso(TOOLKIT_PROC)
            self._marcar_fila(ruta_excel, hoja_excel, orden, "OK", "")

        # Cerrar Major al terminar
        self.log("Cerrando Major...", "info")
        self._matar_proceso(MAJOR_PROC)
        self._matar_proceso(TOOLKIT_PROC)





    # ──────────────────────────────────────────────────────────────────────────
    # Helpers de interacción con la UI
    # ──────────────────────────────────────────────────────────────────────────
    
    def _buscar_cuenta(self, comercio: str) -> bool:
        """
        Busca una cuenta en el sistema.
        Equivale a la sección de búsqueda dentro del FOR del .robot original.
        Intenta dos veces antes de rendirse.
        """
        for intento in range(2):
            # Alt+B dos veces para limpiar búsqueda anterior
            time.sleep(3)
            pyautogui.hotkey("alt", "b")
            time.sleep(0.5)
            pyautogui.hotkey("alt", "b")
            time.sleep(0.5)

            # Esperar botón buscar
            if not self._esperar_imagen("buscar_especiales", timeout=TIMEOUT_VENTANA):
                self.log("No apareció el botón buscar", "error")
                return False

            self._click_imagen("buscar_especiales")
            time.sleep(2)

            # Escribir el número de cuenta en el campo (id:10 en el .robot)
            # Buscamos el campo de texto activo y escribimos
            pyautogui.typewrite(str(comercio), interval=0.05)

            # Esperar y clickar aceptar
            time.sleep(2)
            #self.log("escribiendo comercio y buscando...", "info")
            if self._esperar_imagen("aceptar_especiales", timeout=20):
                #self.log("Acepto comercio...", "info")
                time.sleep(2)
                
                if self._click_imagen("aceptar_especiales"):
                    # Verificar si apareció cartel "no se encuentra"
                    time.sleep(1)
                    if self._imagen_existe("no_encuentra"):
                        self.log(f"No se encontró la cuenta: {comercio}", "warn")
                        self._click_imagen("no_encuentra_aceptar")
                        return False
                    self.log(f"Cuenta encontrada: {comercio}", "ok")
                    return True

            if intento == 0:
                self.log(f"Reintentando búsqueda de: {comercio}", "warn")

        self.log(f"No se pudo buscar la cuenta: {comercio}", "error")
        return False

    def _exportar_excel(self, comercio: str):
        """
        Exporta la tabla de deuda a Excel.
        Equivale a la sección 'Boton Exportar excel' del .robot original.

        El diálogo de guardar NO usa imágenes:
        - El botón Guardar se activa con Alt+G (atajo estándar de Windows)
        - El campo "Nombre:" y el botón "Guardar" del diálogo se manejan
          igual que en el .robot: Wait For Element / RPA.Windows.Click por texto,
          acá reemplazado por _esperar_ventana() + typewrite + Enter.
        """
        output_dir = os.path.join(OUTPUTS_DIR, "Deudas")
        ruta_destino = os.path.join(output_dir, str(comercio))

        # Click derecho en la tabla para abrir el menú contextual
        time.sleep(2)
        self._click_imagen("Tabla_Ingresos")
        time.sleep(0.5)
        try:
            pos = pyautogui.locateCenterOnScreen(
                self._img("Tabla_Ingresos"), confidence=CONFIDENCE
            )
            if pos:
                pyautogui.rightClick(pos)
        except Exception:
            pass

        # Esperar y clickar "Exportar a Excel" (sigue siendo imagen — viene del locators.json)
        if self._esperar_imagen("ExportaraExcel_Ingresos", timeout=20):
            time.sleep(1)
            self._click_imagen("ExportaraExcel_Ingresos")
            time.sleep(3)

        # Guardar: en el .robot era RPA.Windows.Click "Guardar" timeout=20
        self.log("Esperando diálogo de guardar...", "info")
        
        if  self._esperar_imagen("descarga_deuda_ventana", timeout=30):
            time.sleep(1)
            self._click_imagen("guardar_deuda")
            self.log("Diálogo de guardar activo, iniciando exportación...", "info")
    
        time.sleep(2)

        # Esperar el diálogo "Guardar como" con el campo Nombre
        self.log("Esperando campo Nombre de archivo...", "info")
        dialogo_guardar = self._esperar_ventana("Guardar como", timeout=TIMEOUT_GUARDAR)
        if dialogo_guardar:
            try:
                dialogo_guardar.activate()
            except Exception:
                pass
            time.sleep(1)

            pyautogui.hotkey("ctrl", "a")
            time.sleep(0.3)
            try:
                import pyperclip
                pyperclip.copy(ruta_destino)
                pyautogui.hotkey("ctrl", "v")
            except ImportError:
                # Si no hay pyperclip, fallback a typewrite
                pyautogui.typewrite(ruta_destino, interval=0.03)

            time.sleep(0.5)

            # Confirmar con Enter — equivale a RPA.Windows.Click "Guardar"
            pyautogui.press("enter")
            time.sleep(3)

        self.log(f"Excel guardado en Deudas", "ok")



    # ──────────────────────────────────────────────────────────────────────────
    # Helpers de Excel
    # ──────────────────────────────────────────────────────────────────────────

    def _leer_credenciales(self) -> tuple[str, str]:
        """Lee usuario y contraseña del settings.xlsx."""
        wb = load_workbook(SETTINGS_PATH)
        ws = wb["Sheet1"]
        usuario = ws.cell(row=ROW_USUARIO,    column=2).value or ""
        contrasena = ws.cell(row=ROW_CONTRASENA, column=2).value or ""
        return str(usuario), str(contrasena)

    def _leer_config_excel(self) -> tuple[str, str]:
        """Lee el nombre y hoja del Excel de cuentas desde settings.xlsx."""
        wb = load_workbook(SETTINGS_PATH)
        ws = wb["Sheet1"]
        hoja_excel   = ws.cell(row=ROW_HOJA_EXCEL,   column=2).value or "Sheet1"
        nombre_excel = ws.cell(row=ROW_NOMBRE_EXCEL,  column=2).value or ""
        return str(nombre_excel), str(hoja_excel)

    def _marcar_fila(self, ruta: str, hoja: str, orden, estado: str, detalle: str = ""):
        """
        Marca una fila del Excel de cuentas con el estado dado.
        Columna C = estado (OK), Columna D = detalle opcional.
        """
        try:
            wb = load_workbook(ruta)
            ws = wb[hoja]
            fila = int(orden)
            ws.cell(row=fila, column=3, value=estado)
            if detalle:
                ws.cell(row=fila, column=4, value=detalle)
            wb.save(ruta)
        except Exception as e:
            self.log(f"Error marcando fila {orden}: {e}", "warn")

    # ──────────────────────────────────────────────────────────────────────────
    # Control de flujo
    # ──────────────────────────────────────────────────────────────────────────

    def _reiniciar(self, intento: int=0, max_intentos: int=5):
        """
        Reinicia el bot desde el login.
        Equivale al keyword 'Reincio' del .robot original.
        """
        if intento >= max_intentos:
            raise RuntimeError("Máximo de intentos de reinicio alcanzado.")
        self.log(f"Reiniciando bot (intento {intento + 1}/{max_intentos})", "warn")
        self.abrir_major()
        self.recorrer_deudas(intento=intento + 1)
        self.log("Bot finalizado correctamente", "ok")
