"""
App/bot_ejemplo/main.py

Bot de ejemplo para GABI.

Es un script autónomo (no depende de ninguna clase base) que simula el
trabajo de un bot real: imprime su progreso paso a paso y espera unos
segundos entre etapas. Sirve para probar GABI de punta a punta —logs en
vivo, notificaciones, guardado de logs— sin necesidad de un bot productivo.

GABI ejecuta este archivo como un subprocess y captura todo lo que imprime
por stdout/stderr, mostrándolo en el área de log en tiempo real.

Convenciones de log que GABI reconoce y colorea automáticamente:
    INFO:  ...   → azul (información)
    LOG:   ...   → verde (paso completado)
    WARN:  ...   → amarillo (advertencia)
    ERROR: ...   → rojo (error)

Para simular una ejecución fallida (y ver cómo GABI reporta el error),
ejecutá el script con el argumento --fallar:
    python main.py --fallar
"""

import sys
import time


PASOS = [
    ("Conectando al sistema de origen", 1.5),
    ("Autenticando credenciales", 1.0),
    ("Buscando registros pendientes", 2.0),
    ("Procesando 42 registros", 2.5),
    ("Generando reporte de salida", 1.5),
    ("Guardando resultados", 1.0),
]


def log(nivel: str, mensaje: str):
    """Imprime una línea con el prefijo que GABI sabe interpretar."""
    print(f"{nivel}: {mensaje}", flush=True)


def main():
    fallar = "--fallar" in sys.argv

    log("INFO", "Iniciando bot de ejemplo")
    log("INFO", "-" * 40)

    for i, (descripcion, duracion) in enumerate(PASOS, start=1):
        log("INFO", f"[Paso {i}/{len(PASOS)}] {descripcion}...")
        time.sleep(duracion)

        # Simulamos un fallo en la mitad del proceso si se pidió
        if fallar and i == 3:
            log("ERROR", "No se pudo conectar al origen de datos (timeout).")
            log("ERROR", "El bot no puede continuar. Abortando.")
            sys.exit(1)

        log("LOG", f"{descripcion}: OK")

    log("INFO", "-" * 40)
    log("LOG", "Bot de ejemplo finalizado correctamente.")
    sys.exit(0)


if __name__ == "__main__":
    main()