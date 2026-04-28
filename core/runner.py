"""
core/runner.py

Responsable de ejecutar los scripts (.robot / .py) registrados
en el Excel, uno por uno, en un hilo separado del hilo de la UI.

Su flujo:
  1. Lee los bots activos desde excel_utils
  2. Por cada bot, lanza un subprocess (python o según extensión)
  3. Lee stdout y stderr línea a línea y los envía al log via callback
  4. Al terminar todos (o al ser detenido), llama a done_callback

Callbacks recibidos desde PanelMain:
  - log_callback(mensaje, tipo)   → escribe en el área de log
  - done_callback()               → avisa que terminó la ejecución
  - name_callback(nombre)         → actualiza el nombre del bot activo en la UI
"""

import threading
import subprocess
import os
from datetime import datetime
from core.excel_utils import leer_bots, leer_config


class Runner:

    def __init__(self, log_callback, done_callback, name_callback=None):
        self._log          = log_callback
        self._done         = done_callback
        self._set_name     = name_callback   # puede ser None si no se pasa
        self._stop_event   = threading.Event()
        self._proceso_actual = None
        self._lock         = threading.Lock()

        # Hilo daemon: se cierra automáticamente si se cierra la app
        self._thread = threading.Thread(target=self._run, daemon=True)


    # API pública
    def start(self):
        """Inicia la ejecución en el hilo separado."""
        self._thread.start()

    def detener(self):
        """
        Señaliza que debe detenerse.
        Si hay un subprocess corriendo, lo termina inmediatamente.
        """
        self._stop_event.set()
        with self._lock:
            if self._proceso_actual and self._proceso_actual.poll() is None:
                self._proceso_actual.terminate()


    # Lógica principal (corre en el hilo separado)
    def _run(self):
        """
        Itera sobre los bots activos y ejecuta cada uno.
        Es el único método que corre fuera del hilo principal de la UI.
        """
        bots = leer_bots()
        activos = [b for b in bots if b["activo"]]

        if not activos:
            self._log("No hay bots activos para ejecutar.", "warn")
            self._log("Activá al menos un bot en la sección Bots.", "dim")
            self._done()
            return

        self._log(f"Bots a ejecutar: {len(activos)}", "info")
        self._separador()

        for i, bot in enumerate(activos, start=1):

            # ── Chequear si se pidió detener antes de cada bot ───
            if self._stop_event.is_set():
                self._log("Ejecución cancelada antes de iniciar siguiente bot.", "warn")
                break

            nombre = bot["nombre"]
            ruta   = bot["ruta"]

            self._log(f"[{i}/{len(activos)}] Iniciando: {nombre}", "info")

            # Actualizar el nombre en la barra superior del panel
            if self._set_name:
                self._set_name(nombre)

            # ── Verificar que el archivo existe ───
            if not os.path.exists(ruta):
                self._log(f"  Archivo no encontrado: {ruta}", "error")
                self._log(f"  Saltando '{nombre}'...", "warn")
                self._separador()
                continue

            # ── Ejecutar el script ────
            inicio = datetime.now()
            exito  = self._ejecutar_script(ruta)
            duracion = (datetime.now() - inicio).seconds

            if exito:
                self._log(f" '{nombre}' terminó correctamente ({duracion}s)", "ok")
            else:
                self._log(f" '{nombre}' finalizó con errores ({duracion}s)", "error")

            self._separador()

            # Guardar log después de cada bot
            self._guardar_log(nombre, inicio)

        # ── Fin de todos los bots ───
        if self._set_name:
            self._set_name("Esperando para ejecutar...")

        self._done()

    def _ejecutar_script(self, ruta: str) -> bool:
        """
        Lanza el script en un subprocess y captura su output en tiempo real.
        Devuelve True si el proceso terminó con código 0 (sin errores).

        Soporta:
          - .robot  → robot <ruta>
          - .py     → python <ruta>
        """
        # Determinar el comando según la extensión
        ext = os.path.splitext(ruta)[1].lower()
        if ext == ".robot":
            comando = ["robot", ruta]
        elif ext == ".py":
            comando = ["python", ruta]
        else:
            self._log(f"  Extensión no soportada: {ext}", "error")
            return False

        try:
            with self._lock:
                # Lanzamos el proceso
                # - stdout=PIPE: capturamos la salida estándar
                # - stderr=PIPE: capturamos los errores también
                # - text=True: las líneas vienen como str (no bytes)
                # - encoding: importante en Windows para caracteres especiales
                self._proceso_actual = subprocess.Popen(
                    comando,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding="utf-8",
                    errors="replace",      # si hay caracteres raros, los reemplaza
                    cwd=os.path.dirname(os.path.abspath(ruta)),  # working dir = carpeta del script
                )

            # ── Leer stdout y stderr en paralelo ──────────────────────────────
            # Necesitamos dos hilos para leer ambos streams sin que uno bloquee al otro.
            # (Si leyéramos stdout de forma síncrona y el proceso escribe mucho en
            # stderr, el buffer se llena y el proceso se cuelga esperando que lo lean.)

            hilo_stdout = threading.Thread(
                target=self._leer_stream,
                args=(self._proceso_actual.stdout, ""),
                daemon=True,
            )
            hilo_stderr = threading.Thread(
                target=self._leer_stream,
                args=(self._proceso_actual.stderr, "error"),
                daemon=True,
            )

            hilo_stdout.start()
            hilo_stderr.start()

            # Esperar a que ambos streams terminen
            hilo_stdout.join()
            hilo_stderr.join()

            # Esperar a que el proceso termine y obtener el código de salida
            self._proceso_actual.wait()
            return self._proceso_actual.returncode == 0

        except FileNotFoundError:
            # El comando (robot/python) no está en el PATH
            self._log(
                f"  Comando no encontrado. ¿Está 'robot' o 'python' en el PATH?",
                "error"
            )
            return False

        except Exception as e:
            self._log(f"  Error inesperado: {e}", "error")
            return False

        finally:
            with self._lock:
                self._proceso_actual = None

    def _leer_stream(self, stream, tipo: str):
        """
        Lee un stream (stdout o stderr) línea por línea y lo envía al log.
        Corre en su propio hilo para no bloquear.

        Detecta automáticamente el tipo de línea según su contenido:
          - Líneas con ERROR o FAIL  → tipo "error"
          - Líneas con WARN          → tipo "warn"
          - Líneas con INFO o PASS   → tipo "ok"
          - El resto                 → tipo recibido por parámetro
        """
        for linea in iter(stream.readline, ""):

            # Si se pidió detener, dejamos de leer
            if self._stop_event.is_set():
                break

            linea = linea.rstrip("\n")
            if not linea:
                continue

            # Detección automática de tipo según contenido
            tipo_linea = self._detectar_tipo(linea, tipo)
            self._log(linea, tipo_linea)

        stream.close()

    def _detectar_tipo(self, linea: str, tipo_default: str) -> str:
        """
        Analiza el contenido de una línea y devuelve el tipo de log apropiado.
        Funciona tanto para output de Robot Framework como de Python.
        """
        linea_upper = linea.upper()

        if any(p in linea_upper for p in ("| FAIL |", "ERROR", "TRACEBACK", "EXCEPTION")):
            return "error"
        if any(p in linea_upper for p in ("| WARN |", "WARNING", "WARN:")):
            return "warn"
        if any(p in linea_upper for p in ("| PASS |", "OUTPUT:", "LOG:", "REPORT:")):
            return "ok"
        if any(p in linea_upper for p in ("| INFO |", "INFO:")):
            return "info"

        return tipo_default


    # Utilidades
    def _separador(self):
        """Línea divisora en el log para separar visualmente cada bot."""
        self._log("─" * 50, "dim")

    def _guardar_log(self, nombre_bot: str, inicio: datetime):
        """
        Guarda el log de la ejecución en data/logs/log_YYYY-MM-DD.txt
        Lee la ruta de logs desde la configuración del Excel (si existe).
        Si no hay configuración, usa 'data/logs/' por defecto.
        """
        try:
            # Intentar leer la ruta de logs desde el Excel
            config = leer_config()
            ruta_logs = "data/logs"   # default
            for item in config:
                if "log" in item["clave"].lower():
                    ruta_logs = item["valor"]
                    break

            os.makedirs(ruta_logs, exist_ok=True)

            fecha = inicio.strftime("%Y-%m-%d")
            hora_inicio = inicio.strftime("%H:%M:%S")
            nombre_archivo = os.path.join(ruta_logs, f"log_{fecha}.txt")

            with open(nombre_archivo, "a", encoding="utf-8") as f:
                f.write(f"\n{'=' * 60}\n")
                f.write(f"Bot: {nombre_bot}\n")
                f.write(f"Inicio: {hora_inicio}\n")
                f.write(f"Fin: {datetime.now().strftime('%H:%M:%S')}\n")
                f.write(f"{'=' * 60}\n")

        except Exception as e:
            # El log es best-effort: si falla, no queremos romper la ejecución
            self._log(f"Advertencia: no se pudo guardar el log en disco: {e}", "warn")