"""
dev_runner.py — Solo para desarrollo.
Reinicia la app automáticamente cada vez que guardás un archivo .py

Uso:
    python dev_runner.py

No usar en producción. Para distribuir, usar main.py directamente.
"""

import subprocess
import sys
import time
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# ── Configuración ──────────────────────────────────────────────────────────────
CARPETAS_A_MONITOREAR = ["ui", "core"]   # carpetas que watchdog observa
ARCHIVO_MAIN = "main.py"                 # qué ejecutar al detectar cambio
EXTENSION = ".py"                        # solo recargar ante cambios en .py
COOLDOWN = 0.8  # segundos mínimos entre recargas (evita múltiples recargas seguidas)
# ──────────────────────────────────────────────────────────────────────────────


class ReloadHandler(FileSystemEventHandler):
    """
    Se ejecuta cuando watchdog detecta un cambio en el sistema de archivos.
    Mata el proceso anterior y lanza uno nuevo.
    """

    def __init__(self):
        self._proceso = None
        self._ultimo_reload = 0
        self._iniciar_app()

    def _iniciar_app(self):
        """Mata el proceso anterior (si existe) e inicia uno nuevo."""
        if self._proceso and self._proceso.poll() is None:
            self._proceso.terminate()
            try:
                self._proceso.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self._proceso.kill()

        print(f"\n{'─' * 50}")
        print(f"  Iniciando {ARCHIVO_MAIN}...")
        print(f"{'─' * 50}\n")

        # Lanzamos main.py con el mismo intérprete de Python que está corriendo
        self._proceso = subprocess.Popen(
            [sys.executable, ARCHIVO_MAIN],
            cwd=os.getcwd(),
        )

    def on_modified(self, event):
        """Se llama cada vez que se modifica un archivo."""

        # Ignorar carpetas y archivos que no sean .py
        if event.is_directory:
            return
        if not event.src_path.endswith(EXTENSION):
            return

        # Cooldown: evitar múltiples recargas si el editor guarda varias veces
        ahora = time.time()
        if ahora - self._ultimo_reload < COOLDOWN:
            return
        self._ultimo_reload = ahora

        archivo = os.path.relpath(event.src_path)
        print(f"  Cambio detectado: {archivo} → recargando...")
        self._iniciar_app()


def main():
    handler = ReloadHandler()
    observer = Observer()
    print("HOLA")
    # Registrar las carpetas a monitorear
    for carpeta in CARPETAS_A_MONITOREAR:
        if os.path.exists(carpeta):
            observer.schedule(handler, path=carpeta, recursive=True)
        else:
            print(f"  Advertencia: carpeta '{carpeta}' no encontrada, ignorada.")

    # Monitorear también main.py directamente
    observer.schedule(handler, path=".", recursive=False)

    observer.start()
    print(f"  Modo desarrollo activo.")
    print(f"  Monitoreando: {', '.join(CARPETAS_A_MONITOREAR)}")
    print(f"  Guardá cualquier .py para recargar la app.")
    print(f"  Ctrl+C para salir.\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n  Deteniendo dev runner...")
        observer.stop()
        if handler._proceso and handler._proceso.poll() is None:
            handler._proceso.terminate()

    observer.join()


if __name__ == "__main__":
    main()