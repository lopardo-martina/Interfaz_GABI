"""
core/runner.py

Responsable de ejecutar los scripts (.robot / .py) registrados
en settings.json, uno por uno, en un hilo separado del hilo de la UI.

Su flujo:
  1. Lee los bots activos desde core/settings.py
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

from Config.settings import leer_bots, ruta_logs, nombre_equipo
from core.notificador import notif_mail_activa, enviar_mail, render_html


class Runner:

    def __init__(self, log_callback, done_callback, name_callback=None):
        self._log_ui = log_callback
        self._done = done_callback
        self._set_name = name_callback
        self._stop_event = threading.Event()
        self._proceso_actual = None
        self._lock = threading.Lock()
        self._buffer = []
        self._buffer_lock = threading.Lock()
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

    def _log(self, mensaje, tipo=""):
        """Manda la línea a la UI y la guarda en el buffer del bot actual."""
        ts = datetime.now().strftime("%H:%M:%S")
        etiqueta = (tipo.upper() or "LOG").ljust(5)
        with self._buffer_lock:
            self._buffer.append(f"[{ts}] [{etiqueta}] {mensaje}")
        self._log_ui(mensaje, tipo)

    def _reset_buffer(self):
        with self._buffer_lock:
            self._buffer = []

    def _snapshot_buffer(self) -> list[str]:
        with self._buffer_lock:
            return list(self._buffer)

    # Lógica principal (corre en el hilo separado)
    def _run(self):
        """
        Itera sobre los bots activos y ejecuta cada uno.
        Es el único método que corre fuera del hilo principal de la UI.
        """
        bots = leer_bots()
        activos = [b for b in bots if b["activo"]]

        if not activos:
            self._log_ui("No hay bots activos para ejecutar.", "warn")
            self._log_ui("Activá al menos un bot en la sección Bots.", "dim")
            self._done()
            return

        self._log_ui(f"Bots a ejecutar: {len(activos)}", "info")
        self._log_ui("-" * 50, "dim")
        self._separador()

        for i, bot in enumerate(activos, start=1):
            # ── Chequear si se pidió detener antes de cada bot ───
            if self._stop_event.is_set():
                self._log_ui("Ejecución cancelada antes de iniciar siguiente bot.", "warn")
                break

            nombre = bot["nombre"]
            ruta = bot["ruta"]

            self._reset_buffer()
            inicio = datetime.now()

            self._log(f"[{i}/{len(activos)}] Iniciando: {nombre}", "info")

            # Actualizar el nombre en la barra superior del panel
            if self._set_name:
                self._set_name(nombre)

            # ── Verificar que el archivo existe ───
            if not os.path.exists(ruta):
                self._log(f"  Archivo no encontrado: {ruta}", "error")
                self._log(f"  Saltando '{nombre}'...", "warn")
                self._guardar_log(nombre, inicio, False)
                self._notificar(nombre, False, 0, inicio, f"Archivo no encontrado: {ruta}")
                self._separador()
                continue

            # ── Ejecutar el script ────
            exito = self._ejecutar_script(ruta)
            duracion = (datetime.now() - inicio).seconds

            if exito:
                self._log(f" '{nombre}' terminó correctamente ({duracion}s)", "ok")
                self._guardar_log(nombre, inicio, True)
                self._notificar(nombre, True, duracion, inicio, None)
                self._separador()
            else:
                self._log(f" '{nombre}' finalizó con errores ({duracion}s)", "error")
                self._guardar_log(nombre, inicio, False)
                self._notificar(nombre, False, duracion, inicio, self._ultimo_error())
                self._separador()
                break  # Rompemos para que no siga ejecutando el próximo bot

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
                "  Comando no encontrado. ¿Está 'robot' o 'python' en el PATH?",
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

    def _ultimo_error(self, n=15):
        """Devuelve las últimas n líneas del buffer que sean de tipo 'error'."""
        errores = [l for l in self._buffer if "[ERROR]" in l]
        if errores:
            return "\n".join(errores[-n:])
        return "\n".join(self._buffer[-n:])

    def _guardar_log(self, nombre_bot: str, inicio: datetime, exito: bool):
        """
        Guarda el log de la ejecución en <ruta_logs>/log_YYYY-MM-DD.txt
        La ruta de logs se lee desde settings.json (o el default si no está).
        El log es best-effort: si falla, no rompe la ejecución.
        """
        try:
            ruta = ruta_logs()
            os.makedirs(ruta, exist_ok=True)

            fecha = inicio.strftime("%Y-%m-%d")
            hora_inicio = inicio.strftime("%H:%M:%S")
            fin = datetime.now()
            nombre_archivo = os.path.join(ruta, f"log_{fecha}.txt")

            with open(nombre_archivo, "a", encoding="utf-8") as f:
                f.write(f"\n{'=' * 60}\n")
                f.write(f"Bot: {nombre_bot}\n")
                f.write(f"Inicio: {hora_inicio}\n")
                f.write(f"Fin: {fin.strftime('%H:%M:%S')}\n")
                f.write(f"Duración: {(fin - inicio).seconds}s\n")
                f.write(f"Resultado: {'OK' if exito else 'ERROR'}\n")
                f.write(f"{'=' * 60}\n")
                for linea in self._snapshot_buffer():
                    f.write(linea + "\n")
                f.write(f"{'=' * 60}\n")

        except Exception as e:
            self._log_ui(f"Advertencia: no se pudo guardar el log en disco: {e}", "warn")

    # Notificación
    def _notificar(self, nombre: str, exito: bool, duracion: int, fecha_inicio, error: str | None):
        """
        Envía el mail de fin de bot. Best-effort: nunca rompe la ejecución.
        """
        try:
            if not notif_mail_activa():
                return

            estado = "OK" if exito else "ERROR"
            asunto = f"{nombre} finalizó con {estado}"
            fecha = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

            # fecha_inicio llega como datetime desde _run
            if isinstance(fecha_inicio, datetime):
                fecha_inicio_str = fecha_inicio.strftime("%d/%m/%Y %H:%M:%S")
            else:
                fecha_inicio_str = str(fecha_inicio)

            equipo = nombre_equipo() or os.environ.get("COMPUTERNAME", "Desconocido")

            cuerpo = (
                f"Bot:          {nombre}\n"
                f"Resultado:    {estado}\n"
                f"Duración:     {duracion}s\n"
                f"Fecha_inicio: {fecha_inicio_str}\n"
                f"Fecha_fin:    {fecha}\n"
                f"Equipo:       {equipo}\n"
            )
            if error:
                cuerpo += f"\n{'-' * 50}\nDetalle:\n{error}\n"

            # HTML
            cuerpo_html = render_html(nombre, exito, duracion, fecha, fecha_inicio_str, equipo, error)

            ok, detalle = enviar_mail(asunto, cuerpo, cuerpo_html)
            self._log_ui(detalle, "ok" if ok else "warn")

        except Exception as e:
            self._log_ui(f"No se pudo notificar por mail: {e}", "warn")