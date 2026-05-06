"""
core/bot_base.py

Clase base para todos los bots de BABOT.

Contiene los helpers genéricos compartidos entre bots:
  - Interacción con la UI (imágenes, texto, ventanas)
  - Control de procesos
  - Fechas
  - Control de flujo (stop, reinicio)

Cada bot hereda de BotBase y solo implementa su lógica específica.
Las constantes propias de cada bot (MAJOR_EXE, SETTINGS_PATH, IMAGES_DIR, etc.)
se definen en el config.py de cada bot y se pasan o acceden desde el bot hijo.
"""

import os
import time
import psutil
import pyautogui
import numpy as np
import cv2
import pygetwindow as gw
from datetime import datetime, timedelta
from pywinauto import Application, Desktop

pyautogui.PAUSE = 0.1
pyautogui.FAILSAFE = True


class BotBase:
    """
    Clase base para todos los bots de BABOT.

    Uso:
        class BotMiBot(BotBase):
            def ejecutar(self):
                self.abrir_major()
                self.mi_logica()
    """

    def __init__(self, logger=None, stop_event=None):
        self.log        = logger or (lambda msg, tipo="": print(f"[{tipo.upper()}] {msg}"))
        self.stop_event = stop_event

    # ──────────────────────────────────────────────────────────────────────────
    # Helpers de interacción con la UI — imágenes
    # ──────────────────────────────────────────────────────────────────────────

    def _img(self, nombre: str) -> str:
        """
        Devuelve la ruta completa de una imagen de referencia.
        Requiere que el bot hijo defina self.IMAGES_DIR o use el de su config.
        """
        return os.path.join(self.IMAGES_DIR, f"{nombre}.png")

    def _mejor_match(self, nombre: str, min_score: float = None):
        """
        Busca la imagen en pantalla usando OpenCV y devuelve el centro del
        match con mayor score, solo si supera min_score.
        Devuelve (x, y) o None si no supera el umbral.
        """
        score = min_score if min_score is not None else self.CONFIDENCE
        try:
            screenshot_gray = cv2.cvtColor(
                np.array(pyautogui.screenshot()), cv2.COLOR_RGB2GRAY
            )
            ruta = self._img(nombre)
            if not os.path.exists(ruta):
                self.log(f"Imagen no encontrada: {ruta}", "warn")
                return None
            template = cv2.imread(ruta, cv2.IMREAD_GRAYSCALE)
            if template is None:
                self.log(f"No se pudo leer imagen: {nombre}", "error")
                return None
            resultado = cv2.matchTemplate(
                screenshot_gray, template, cv2.TM_CCOEFF_NORMED
            )
            _, max_val, _, max_loc = cv2.minMaxLoc(resultado)
            if max_val < score:
                return None
            h, w = template.shape
            return (max_loc[0] + w // 2, max_loc[1] + h // 2)
        except Exception as e:
            self.log(f"Error en _mejor_match '{nombre}': {e}", "error")
            return None

    def _imagen_existe(self, nombre: str) -> bool:
        """Devuelve True si la imagen tiene un match por encima del umbral."""
        return self._mejor_match(nombre) is not None

    def _esperar_imagen(self, nombre: str, timeout: int = 30) -> bool:
        """
        Espera hasta que la imagen aparezca en pantalla.
        Devuelve True si apareció dentro del timeout, False si no.
        """
        fin = time.time() + timeout
        while time.time() < fin:
            if self._imagen_existe(nombre):
                return True
            time.sleep(1)
        return False

    def _click_imagen(self, nombre: str, doble: bool = False) -> bool:
        """
        Hace click en el match de mayor score.
        Solo clickea si el score supera el umbral — nunca clickea algo dudoso.
        Devuelve True si pudo hacer click, False si no encontró match confiable.
        """
        pos = self._mejor_match(nombre)
        if pos:
            if doble:
                pyautogui.doubleClick(pos)
            else:
                pyautogui.click(pos)
            self.log(f"Click en '{nombre}'.", "info")
            return True
        return False

    def _boton_texto(self, template_path: str, hacer_click: bool = True, doble_click: bool = False) -> bool:
        """
        Busca un elemento por ruta completa de imagen (no alias).
        Usado internamente por _encontrar_una_imagen para recorrer listas.
        """
        try:
            screenshot_gray = cv2.cvtColor(
                np.array(pyautogui.screenshot()), cv2.COLOR_RGB2GRAY
            )
            template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
            if template is None:
                self.log(f"No se pudo leer template: {template_path}", "error")
                return False
            resultado = cv2.matchTemplate(
                screenshot_gray, template, cv2.TM_CCOEFF_NORMED
            )
            _, max_val, _, max_loc = cv2.minMaxLoc(resultado)
            if max_val >= self.CONFIDENCE:
                if hacer_click:
                    h, w = template.shape
                    cx = max_loc[0] + w // 2
                    cy = max_loc[1] + h // 2
                    if doble_click:
                        pyautogui.doubleClick(cx, cy)
                    else:
                        pyautogui.click(cx, cy)
                return True
            self.log(f"No se encontró el template: {template_path}", "warn")
            return False
        except Exception as e:
            self.log(f"Error en _boton_texto: {e}", "error")
            return False

    def _encontrar_una_imagen(self, nombre: str, tecla: str, max_intentos: int = 1000) -> bool:
        """
        Busca un elemento recorriendo la lista con una tecla hasta encontrarlo.
        Equivale a 'Encontrar Una Imagen' del .robot original.
        """
        template_path = self._img(nombre)
        for _ in range(max_intentos):
            if self._boton_texto(template_path, hacer_click=True, doble_click=True):
                self.log(f"Elemento '{nombre}' encontrado y seleccionado.", "ok")
                return True
            pyautogui.press(tecla)
            time.sleep(0.5)
        self.log(f"No se encontró '{nombre}' tras {max_intentos} intentos.", "warn")
        return False

    # ──────────────────────────────────────────────────────────────────────────
    # Helpers de interacción con la UI — ventanas y texto
    # ──────────────────────────────────────────────────────────────────────────

    def _esperar_ventana(self, titulo: str, timeout: int = 30):
        """
        Espera hasta que aparezca una ventana cuyo título contenga 'titulo'.
        Devuelve la ventana si la encontró, None si venció el timeout.
        """
        fin = time.time() + timeout
        while time.time() < fin:
            ventanas = gw.getWindowsWithTitle(titulo)
            if ventanas:
                return ventanas[0]
            time.sleep(1)
        return None

    def _click_por_texto(self, texto: str, timeout: int = 30, ventana_re: str = None):
        """
        Hace click en un control buscándolo por título con pywinauto.
        Si ventana_re se especifica, busca el control dentro de esa ventana.
        Si no, busca en todas las ventanas abiertas del escritorio.
        Equivale a RPA.Windows.Click por nombre/texto del .robot original.
        """
        fin = time.time() + timeout
        while time.time() < fin:
            try:
                if ventana_re:
                    app = Application(backend="win32").connect(title_re=ventana_re)
                    win = app.window(title_re=ventana_re)
                    win.child_window(title=texto).click_input()
                else:
                    Desktop(backend="win32").window(best_match=texto).click_input()
                self.log(f"Click en '{texto}'.", "info")
                return
            except Exception:
                time.sleep(1)
        raise TimeoutError(f"No se encontró el elemento '{texto}' en {timeout}s.")

    def _esperar_archivo(self, ruta: str, timeout: int = 120):
        """Espera hasta que el archivo exista en disco."""
        self.log(f"Esperando archivo: {ruta}", "info")
        fin = time.time() + timeout
        while time.time() < fin:
            if os.path.exists(ruta):
                self.log("Archivo encontrado.", "ok")
                return
            time.sleep(2)
        raise TimeoutError(f"El archivo no apareció en {timeout}s: {ruta}")

    # ──────────────────────────────────────────────────────────────────────────
    # Helpers de procesos
    # ──────────────────────────────────────────────────────────────────────────

    def _proceso_existe(self, nombre: str) -> bool:
        """Devuelve True si hay un proceso corriendo con ese nombre."""
        for proc in psutil.process_iter(["name"]):
            if proc.info["name"] and proc.info["name"].lower() == nombre.lower():
                return True
        return False

    def _matar_proceso(self, nombre: str):
        """Termina todos los procesos con ese nombre."""
        for proc in psutil.process_iter(["name"]):
            if proc.info["name"] and proc.info["name"].lower() == nombre.lower():
                try:
                    proc.terminate()
                    self.log(f"Proceso terminado: {nombre}", "dim")
                except Exception:
                    pass

    # ──────────────────────────────────────────────────────────────────────────
    # Helpers de fechas
    # ──────────────────────────────────────────────────────────────────────────

    def _normalizar_fecha(self, valor) -> str:
        """
        Convierte cualquier valor que pueda venir de openpyxl a string YYYY-MM-DD.
        Maneja: None, string vacío, string "None", datetime, date, strings con fecha.
        Devuelve "" si el valor es vacío o inválido.
        """
        if valor is None:
            return ""
        if isinstance(valor, datetime):
            return valor.strftime("%Y-%m-%d")
        from datetime import date as date_type
        if isinstance(valor, date_type):
            return valor.strftime("%Y-%m-%d")
        s = str(valor).strip()
        if s.lower() in ("", "none"):
            return ""
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
            try:
                return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
            except ValueError:
                continue
        self.log(f"No se pudo parsear la fecha: '{s}'", "warn")
        return ""

    def _fecha_mas_un_dia(self, fecha_str: str) -> str:
        """Suma un día a una fecha en formato YYYY-MM-DD."""
        return (datetime.strptime(fecha_str, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")

    def _ayer(self) -> str:
        """Devuelve la fecha de ayer en formato YYYY-MM-DD."""
        return (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d")

    # ──────────────────────────────────────────────────────────────────────────
    # Helpers de Excel
    # ──────────────────────────────────────────────────────────────────────────

    def _try_convert_to_int(self, valor):
        """Convierte a int si es posible, si no devuelve el valor original."""
        try:
            return int(valor)
        except (ValueError, TypeError):
            return valor

    # ──────────────────────────────────────────────────────────────────────────
    # Control de flujo
    # ──────────────────────────────────────────────────────────────────────────

    def _check_stop(self):
        """
        Verifica si se solicitó detener el bot.
        Lanza InterruptedError que el runner captura limpiamente.
        """
        if self.stop_event and self.stop_event.is_set():
            raise InterruptedError("Bot detenido por el usuario.")