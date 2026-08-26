"""
ui/panels/panel_bots.py

Panel de gestión de bots. Permite:
  - Ver todos los bots registrados en settings.json
  - Activar / desactivar cada bot con un toggle
  - Agregar un bot nuevo (nombre + ruta con selector de archivo)
  - Eliminar un bot existente

Los cambios se guardan en settings.json en tiempo real
(cada toggle y cada eliminación guarda automáticamente).

Al agregar un bot, su bloque 'config' arranca vacío: las variables propias
se agregan después a mano en el settings.json y el usuario edita sus valores
desde el panel de Configuración.
"""

import os
import customtkinter as ctk
from tkinter import filedialog, messagebox
from config.almacenamiento import leer_bots, guardar_bots, agregar_bot, eliminar_bot


class PanelBots(ctk.CTkFrame):

    def __init__(self, parent, colors: dict, main_window):
        super().__init__(parent, fg_color=colors["bg_panel"], corner_radius=0)

        self.colors      = colors
        self.main_window = main_window

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._toggle_vars = []

        self._build_header()
        self._build_lista()
        self._build_footer()
        self._cargar_bots()

    # Construcción de la UI
    def _build_header(self):
        from ui.components import boton_campana

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=16, pady=(18, 8))
        header.grid_columnconfigure(0, weight=1)

        # Bloque título + contador (apilados a la izquierda)
        titulo_box = ctk.CTkFrame(header, fg_color="transparent")
        titulo_box.grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            titulo_box,
            text="BOTS REGISTRADOS",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=self.colors["text_primary"],
            anchor="w",
        ).pack(anchor="w")

        self.contador_label = ctk.CTkLabel(
            titulo_box,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=self.colors["text_muted"],
            anchor="w",
        )
        self.contador_label.pack(anchor="w")

        # Campana a la derecha
        boton_campana(
            header, self.colors, self.main_window.abrir_config_notificador
        ).grid(row=0, column=1, sticky="e")

    def _build_lista(self):
        self.scroll = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=self.colors["bg_card"],
            scrollbar_button_hover_color=self.colors["border"],
        )
        self.scroll.grid(row=1, column=0, sticky="nsew", padx=16, pady=4)
        self.scroll.grid_columnconfigure(0, weight=1)

    def _build_footer(self):
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.grid(row=2, column=0, sticky="ew", padx=16, pady=(4, 14))
        footer.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(
            footer,
            text="AGREGAR BOT",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=44,
            corner_radius=10,
            fg_color=self.colors["bg_card"],
            text_color=self.colors["text_primary"],
            hover_color=self.colors["border"],
            border_width=1,
            border_color=self.colors["border"],
            command=self._abrir_dialogo_agregar,
        ).grid(row=0, column=0, sticky="ew", padx=(0, 6))

        ctk.CTkButton(
            footer,
            text="GUARDAR CAMBIOS",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=44,
            corner_radius=10,
            fg_color=self.colors["accent"],
            text_color="#ffffff",
            hover_color=self.colors["accent_hover"],
            command=self._guardar_cambios,
        ).grid(row=0, column=1, sticky="ew", padx=(6, 0))

    # ──────────────────────────────────────────────────────────────────────────
    # Carga y renderizado
    # ──────────────────────────────────────────────────────────────────────────

    def _cargar_bots(self):
        for widget in self.scroll.winfo_children():
            widget.destroy()
        self._toggle_vars = []

        bots = leer_bots()

        if not bots:
            ctk.CTkLabel(
                self.scroll,
                text="No hay bots registrados.\nUsá 'Agregar bot' para empezar.",
                font=ctk.CTkFont(size=13),
                text_color=self.colors["text_muted"],
                justify="center",
            ).pack(expand=True, pady=40)
            self._actualizar_contador(bots)
            return

        # Contenedor único con borde que envuelve todas las filas (estilo mockup)
        self.contenedor_bots = ctk.CTkFrame(
            self.scroll,
            fg_color=self.colors["bg_card"],
            corner_radius=12,
            border_width=1,
            border_color=self.colors["border"],
        )
        self.contenedor_bots.grid(row=0, column=0, sticky="ew", pady=(2, 4))
        self.contenedor_bots.grid_columnconfigure(0, weight=1)

        for i, bot in enumerate(bots):
            self._render_fila_bot(i, bot, es_ultima=(i == len(bots) - 1))

        self._actualizar_contador(bots)

    def _render_fila_bot(self, indice: int, bot: dict, es_ultima: bool = False):
        """
        Renderiza una fila de bot dentro del contenedor compartido.
        Las filas se separan con una línea divisoria (salvo la última).
        """
        fila = ctk.CTkFrame(self.contenedor_bots, fg_color="transparent")
        fila.grid(row=indice * 2, column=0, sticky="ew", padx=6, pady=2)
        fila.grid_columnconfigure(1, weight=1)

        # Toggle
        var = ctk.BooleanVar(value=bot["activo"])
        self._toggle_vars.append(var)

        ctk.CTkSwitch(
            fila,
            text="",
            variable=var,
            width=44,
            button_color=self.colors["accent"],
            button_hover_color=self.colors["accent_hover"],
            progress_color=self.colors["accent"],
            command=self._actualizar_contador_live,
        ).grid(row=0, column=0, rowspan=2, padx=10)


        # Nombre y ruta del bot
        col_nombre = ctk.CTkFrame(fila, fg_color="transparent")
        col_nombre.grid(row=0, column=1, sticky="ew", padx=4, pady=(15, 0))
        col_nombre.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            col_nombre,
            text=bot["nombre"] or "(sin nombre)",
            font=ctk.CTkFont(size=16),
            text_color=self.colors["text_primary"],
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

        # Ruta del bot
        ctk.CTkLabel(
            col_nombre,
            text=self._truncar_ruta(bot["ruta"]),
            font=ctk.CTkFont(size=11),
            text_color=self.colors["text_dim"],
            anchor="w",
        ).grid(row=1, column=0, sticky="w")

        # Botón eliminar (ícono de basurero)
        ctk.CTkButton(
            fila,
            text="🗑️",
            font=ctk.CTkFont(size=15),
            width=5,
            height=34,
            corner_radius=10,
            fg_color="transparent",
            text_color=self.colors["text_muted"],
            hover_color=self.colors["danger"],
            command=lambda i=indice: self._confirmar_eliminar(i),
        ).grid(row=0, column=2, padx=(0,1))

        # Línea divisoria entre filas (no en la última)
        if not es_ultima:
            ctk.CTkFrame(
                self.contenedor_bots, height=1, fg_color=self.colors["border"], border_width=1,
            ).grid(row=indice * 2 + 1, column=0, sticky="ew", padx=12)

    # ──────────────────────────────────────────────────────────────────────────
    # Acciones
    # ──────────────────────────────────────────────────────────────────────────

    def _guardar_cambios(self):
        bots = leer_bots()

        if len(bots) != len(self._toggle_vars):
            self._cargar_bots()
            return

        for bot, var in zip(bots, self._toggle_vars):
            bot["activo"] = var.get()

        ok = guardar_bots(bots)

        if ok:
            self.main_window.set_status("● Bots guardados", self.colors["log_ok"])
            self.after(2000, lambda: self.main_window.set_status("● En espera"))
        else:
            messagebox.showerror(
                "Error",
                "No se pudo guardar en settings.json.\n"
                "Verificá los permisos del archivo."
            )

    def _confirmar_eliminar(self, indice: int):
        bots   = leer_bots()
        nombre = bots[indice]["nombre"] if indice < len(bots) else "este bot"

        if messagebox.askyesno(
            "Eliminar bot",
            f"¿Eliminar '{nombre}'?\n\nEsta acción no se puede deshacer.",
        ):
            eliminar_bot(indice)
            self._cargar_bots()

    def _abrir_dialogo_agregar(self):
        dialogo = _DialogoAgregarBot(self, self.colors)
        self.wait_window(dialogo)

        if dialogo.resultado:
            nombre, ruta = dialogo.resultado
            agregar_bot(nombre, ruta)
            self._cargar_bots()

    # ──────────────────────────────────────────────────────────────────────────
    # Utilidades
    # ──────────────────────────────────────────────────────────────────────────

    def _actualizar_contador(self, bots: list):
        total   = len(bots)
        activos = sum(1 for b in bots if b["activo"])
        self.contador_label.configure(
            text=f"{activos} activo{'s' if activos != 1 else ''} / {total} total"
        )

    def _actualizar_contador_live(self):
        activos = sum(1 for v in self._toggle_vars if v.get())
        total   = len(self._toggle_vars)
        self.contador_label.configure(
            text=f"{activos} activo{'s' if activos != 1 else ''} / {total} total"
        )

    def _truncar_ruta(self, ruta: str, max_chars: int = 55) -> str:
        if not ruta:
            return "(sin ruta)"
        if len(ruta) <= max_chars:
            return ruta
        return "..." + ruta[-(max_chars - 3):]


# ──────────────────────────────────────────────────────────────────────────────
# Diálogo modal: Agregar bot
# ──────────────────────────────────────────────────────────────────────────────

class _DialogoAgregarBot(ctk.CTkToplevel):
    """
    Ventana modal para agregar un bot nuevo.
    Al cerrarse, self.resultado contiene (nombre, ruta) o None si canceló.
    """

    def __init__(self, parent, colors: dict):
        super().__init__(parent)

        self.colors    = colors
        self.resultado = None

        self.title("Agregar bot")
        self.geometry("420x240")
        self.resizable(False, False)
        self.configure(fg_color=colors["bg_app"])
        self.transient(parent)
        self.grab_set()

        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)

        # Nombre
        ctk.CTkLabel(
            self, text="Nombre del bot",
            font=ctk.CTkFont(size=12),
            text_color=self.colors["text_muted"], anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=20, pady=(20, 4))

        self.entry_nombre = ctk.CTkEntry(
            self, placeholder_text="Ej: DeudaDescargas",
            height=36, corner_radius=7,
            fg_color=self.colors["bg_card"],
            border_color=self.colors["border"],
            text_color=self.colors["text_primary"],
        )
        self.entry_nombre.grid(row=1, column=0, sticky="ew", padx=20)

        # Ruta
        ctk.CTkLabel(
            self, text="Archivo del script (.robot o .py)",
            font=ctk.CTkFont(size=12),
            text_color=self.colors["text_muted"], anchor="w",
        ).grid(row=2, column=0, sticky="w", padx=20, pady=(14, 4))

        ruta_frame = ctk.CTkFrame(self, fg_color="transparent")
        ruta_frame.grid(row=3, column=0, sticky="ew", padx=20)
        ruta_frame.grid_columnconfigure(0, weight=1)

        self.entry_ruta = ctk.CTkEntry(
            ruta_frame, placeholder_text="Seleccioná el archivo...",
            height=36, corner_radius=7,
            fg_color=self.colors["bg_card"],
            border_color=self.colors["border"],
            text_color=self.colors["text_primary"],
        )
        self.entry_ruta.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        ctk.CTkButton(
            ruta_frame, text="📂", width=36, height=36,
            corner_radius=7,
            fg_color=self.colors["bg_card"],
            hover_color="#333338",
            border_width=1,
            border_color=self.colors["border"],
            command=self._seleccionar_archivo,
        ).grid(row=0, column=1)

        # Botones
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=4, column=0, sticky="ew", padx=20, pady=(18, 0))
        btn_frame.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(
            btn_frame, text="Cancelar", height=36, corner_radius=7,
            fg_color=self.colors["bg_card"],
            text_color=self.colors["text_muted"],
            hover_color="#333338",
            border_width=1, border_color=self.colors["border"],
            command=self.destroy,
        ).grid(row=0, column=0, sticky="ew", padx=(0, 6))

        ctk.CTkButton(
            btn_frame, text="Agregar", height=36, corner_radius=7,
            fg_color=self.colors["accent"],
            hover_color="#1560a0",
            command=self._confirmar,
        ).grid(row=0, column=1, sticky="ew", padx=(6, 0))

    def _seleccionar_archivo(self):
        ruta = filedialog.askopenfilename(
            title="Seleccionar script",
            filetypes=[
                ("Scripts Robot/Python", "*.robot *.py"),
                ("Robot Framework", "*.robot"),
                ("Python", "*.py"),
                ("Todos", "*.*"),
            ]
        )
        if ruta:
            self.entry_ruta.delete(0, "end")
            self.entry_ruta.insert(0, ruta.replace("/", "\\"))

    def _confirmar(self):
        nombre = self.entry_nombre.get().strip()
        ruta   = self.entry_ruta.get().strip()

        if not nombre:
            messagebox.showwarning("Campo requerido", "Ingresá un nombre para el bot.")
            return
        if not ruta:
            messagebox.showwarning("Campo requerido", "Seleccioná el archivo del script.")
            return
        if not os.path.exists(ruta):
            messagebox.showwarning(
                "Archivo no encontrado",
                f"No se encontró el archivo:\n{ruta}\n\nVerificá que la ruta sea correcta."
            )
            return

        self.resultado = (nombre, ruta)
        self.destroy()