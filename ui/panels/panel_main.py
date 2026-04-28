import tkinter as tk
import customtkinter as ctk
from datetime import datetime


class PanelMain(ctk.CTkFrame):
    """
    Panel principal de GABI.

    Muestra:
    - Barra superior con el nombre del bot activo y su estado
    - Área de log con colores por tipo de mensaje
    - Botones Iniciar y Detener
    """

    def __init__(self, parent, colors: dict, main_window):
        super().__init__(parent, fg_color=colors["bg_panel"], corner_radius=0)

        self.colors = colors
        self.main_window = main_window  # referencia a MainWindow para set_status()

        # Expandir filas y columnas para que el log ocupe todo el espacio disponible
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._build_script_bar()
        self._build_log_area()
        self._build_buttons()


    """Construcción de la UI"""
    def _build_script_bar(self):
        """
        Barra superior que muestra qué bot está activo y su estado.
        Se actualiza durante la ejecución.
        """
        bar = ctk.CTkFrame(
            self,
            fg_color=self.colors["bg_sidebar"],
            corner_radius=10,
        )
        bar.grid(row=0, column=0, sticky="ew", padx=10, pady=(16, 5))
        bar.grid_columnconfigure(0, weight=1)

        # Etiqueta "BOT ACTIVO"
        ctk.CTkLabel(
            bar,
            text="BOT ACTIVO",
            font=ctk.CTkFont(size=12),
            text_color=self.colors["text_dim"],
        ).grid(row=0, column=0, sticky="w", padx=14, pady=(6, 0))

        # Nombre del script — se actualiza durante la ejecución
        self.script_name_label = ctk.CTkLabel(
            bar,
            text="Esperando para ejecutar...",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=self.colors["accent_light"],
        )
        self.script_name_label.grid(row=1, column=0, sticky="w", padx=14, pady=(0, 6))

        # Botn de estado
        self.status_chip = ctk.CTkLabel(
            bar,
            text="En espera",
            font=ctk.CTkFont(size=10),
            fg_color=self.colors["bg_app"],
            text_color=self.colors["text_dim"],
            corner_radius=999,
            padx=6,
            pady=4,
        )
        self.status_chip.grid(row=0, column=1, rowspan=2, padx=12, pady=10)

    def _build_log_area(self):
        """
        Área de texto donde se muestra el output del bot en tiempo real.

        Se usa tk.Text (no CTkTextbox) porque se tags de color
        para distinguir tipos de mensaje (info, ok, warning, error).
        """
        log_frame = ctk.CTkFrame(
            self,
            fg_color="#111113",   # más oscuro que el fondo para destacar
            corner_radius=10,
        )
        log_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=4)
        log_frame.grid_rowconfigure(1, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)

        # ── Encabezado del log ──
        header = ctk.CTkFrame(log_frame, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 4))

        ctk.CTkLabel(
            header,
            text="LOG DE EJECUCIÓN",
            font=ctk.CTkFont(size=12),
            text_color=self.colors["text_dim"],
        ).pack(side="left")

        # Botón Limpiar log
        ctk.CTkButton(
            header,
            text="Limpiar",
            font=ctk.CTkFont(size=10),
            height=22,
            width=60,
            corner_radius=999,
            fg_color=self.colors["bg_card"],
            text_color=self.colors["text_muted"],
            hover_color=self.colors["accent_dark"],
            command=self._clear_log,
        ).pack(side="right")

        # ── Texto del log ──
        self.log_text = tk.Text(
            log_frame,
            bg="#111113",
            fg=self.colors["text_muted"],
            font=("Consolas", 10),
            wrap="word",
            state="disabled",       # solo lectura; se habilita al escribir
            cursor="arrow",
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
            padx=12,
            pady=6,
        )
        self.log_text.grid(row=1, column=0, sticky="nsew", padx=0, pady=(0, 10))

        # Scrollbar vertical
        scrollbar = ctk.CTkScrollbar(log_frame, command=self.log_text.yview)
        scrollbar.grid(row=1, column=1, sticky="ns", pady=(0, 8))
        self.log_text.configure(yscrollcommand=scrollbar.set)

        # ── Tags de color por tipo de mensaje ───
        # Cada tipo de log tiene su propio color y se aplica con tag_add()
        self.log_text.tag_configure("info",  foreground=self.colors["log_info"])
        self.log_text.tag_configure("ok",    foreground=self.colors["log_ok"])
        self.log_text.tag_configure("warn",  foreground=self.colors["log_warn"])
        self.log_text.tag_configure("error", foreground=self.colors["log_error"])
        self.log_text.tag_configure("dim",   foreground=self.colors["text_dim"])

        # Mensaje inicial en el log
        self._log("Sistema iniciado.", "dim")
        self._log("Leyendo configuración desde settings.xlsx...", "info")
        self._log("Esperando orden de ejecución.", "dim")

    def _build_buttons(self):
        """Botones Iniciar y Detener en la parte inferior."""

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=2, column=0, sticky="ew", padx=16, pady=(6, 14))
        btn_frame.grid_columnconfigure((0, 1), weight=1)

        # ── Botón Iniciar ────
        self.btn_iniciar = ctk.CTkButton(
            btn_frame,
            text="▶  Iniciar",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=40,
            corner_radius=12,
            fg_color=self.colors["accent"],
            hover_color=self.colors["accent_dark"],
            command=self._on_iniciar,
        )
        self.btn_iniciar.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        # ── Botón Detener ───
        self.btn_detener = ctk.CTkButton(
            btn_frame,
            text="■  Detener",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=40,
            corner_radius=12,
            fg_color=self.colors["danger"],
            text_color=self.colors["danger_text"],
            hover_color="#4a2020",
            state="disabled",        # deshabilitado hasta que inicie
            command=self._on_detener,
        )
        self.btn_detener.grid(row=0, column=1, sticky="ew", padx=(6, 0))


    """Métodos de log"""
    def _log(self, mensaje: str, tipo: str = ""):
        """
        Inserta una línea en el log con timestamp y color según el tipo.

        Tipos disponibles: "info", "ok", "warn", "error", "dim"
        Si tipo es vacío, usa el color de texto por defecto.

        Este método es thread-safe: usa after() para ejecutar en el hilo
        principal de la UI (necesario cuando lo llama el runner en otro hilo).
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        linea = f"[{timestamp}] {mensaje}\n"

        def _insertar():
            self.log_text.configure(state="normal")
            self.log_text.insert("end", linea, tipo)
            self.log_text.configure(state="disabled")
            self.log_text.see("end")  # scroll automático al final

        # after(0, fn) encola la función en el hilo principal de Tk
        self.log_text.after(0, _insertar)

    def log(self, mensaje: str, tipo: str = ""):
        """Método público para que el runner pueda escribir en el log."""
        self._log(mensaje, tipo)

    def _clear_log(self):
        """Limpia todo el contenido del área de log."""
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")


    """funciones de los botones"""
    def _on_iniciar(self):
        """
        Prepara la UI para la ejecución e inicia el runner.
        """
        from core.runner import Runner
 
        self.btn_iniciar.configure(state="disabled")
        self.btn_detener.configure(state="normal")
        self._set_running_state(True)
 
        self._clear_log()
        self._log("Iniciando ejecución...", "info")
 
        # Runner recibe tres callbacks:
        #   log_callback  → escribe líneas en el área de log
        #   done_callback → avisa cuando terminó toda la ejecución
        #   name_callback → actualiza el nombre del bot activo en la barra superior
        self._runner = Runner(
            log_callback=self.log,
            done_callback=self._on_ejecucion_terminada,
            name_callback=self._on_nombre_bot,
        )
        self._runner.start()
 
    def _on_nombre_bot(self, nombre: str):
        """
        Callback que llama el runner cuando cambia el bot activo.
        Corre desde otro hilo → usamos after() para tocar la UI.
        """
        self.after(0, lambda: self.set_script_name(nombre))
 
    def _on_detener(self):
        """Detiene la ejecución en curso."""
        if hasattr(self, "_runner"):
            self._runner.detener()
        self._log("Detenido por el usuario.", "warn")
        self._set_running_state(False)
 
    def _on_ejecucion_terminada(self):
        """
        Callback que llama el runner cuando termina (con éxito o error).
        Se ejecuta desde otro hilo, por eso usamos after() para tocar la UI.
        """
        self.after(0, lambda: self._set_running_state(False))
        self.after(0, lambda: self._log("Ejecución finalizada.", "ok"))
 
 


    """Estado visual"""
    def _set_running_state(self, running: bool):
        """Actualiza todos los elementos visuales según si está ejecutando o no."""
        if running:
            self.status_chip.configure(
                text="Ejecutando",
                fg_color=self.colors["accent_dark"],
                text_color=self.colors["accent_light"],
            )
            self.main_window.set_status("● Ejecutando...", self.colors["log_info"])
        else:
            self.btn_iniciar.configure(state="normal")
            self.btn_detener.configure(state="disabled")
            self.status_chip.configure(
                text="En espera",
                fg_color=self.colors["bg_app"],
                text_color=self.colors["text_dim"],
            )
            self.main_window.set_status("● En espera", self.colors["text_dim"])

    def set_script_name(self, nombre: str):
        """
        Actualiza el nombre del bot activo en la barra superior.
        Lo llama el runner cuando empieza a ejecutar cada script.
        """
        self.script_name_label.configure(text=nombre)