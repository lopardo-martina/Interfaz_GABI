"""
ui/panels/panel_config.py

Panel de configuración. Se divide en dos zonas:

  1. CONFIGURACIÓN GLOBAL (fija, siempre visible):
     app / smtp / rutas — las credenciales, notificaciones y ruta de logs
     que usa GABI en general.

  2. CONFIGURACIÓN POR BOT (dinámica):
     Cada bot tiene su propio bloque 'config' con sus variables.
     - Si hay un solo bot, se muestran sus variables directamente.
     - Si hay más de uno, aparecen pestañas (una por bot) con CTkTabview.

El panel solo EDITA valores de claves que ya existen en el settings.json.
Para AGREGAR una variable nueva a un bot, se edita el settings.json a mano
(la estructura la define el desarrollador, los valores los ajusta el usuario).
"""

import customtkinter as ctk
from tkinter import messagebox
from config.almacenamiento import (
    leer_config_global,
    guardar_config_global,
    leer_bots,
    guardar_config_de_bot,
)


# Etiquetas legibles para las claves de la config global.
# Si una clave no está acá, se muestra la clave tal cual.
_LABELS_GLOBAL = {
    "nombre_bot":   "Nombre del sistema",
    "equipo":       "Equipo",
    "user":         "Usuario SMTP",
    "pass":         "Contraseña SMTP",
    "mail_destino": "Destinatarios",
    "notif_mail":   "Notificar por mail",
    "logs":         "Carpeta de logs",
}


class PanelConfig(ctk.CTkFrame):

    def __init__(self, parent, colors: dict, main_window):
        super().__init__(parent, fg_color=colors["bg_panel"], corner_radius=0)

        self.colors      = colors
        self.main_window = main_window

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Referencias a los entries/switches para poder leerlos al guardar.
        # Global: { "app": {clave: widget}, "smtp": {...}, "rutas": {...} }
        # Bots:   { "NombreBot": {clave: widget}, ... }
        self._widgets_global = {}
        self._widgets_bots = {}

        self._build_header()
        self._build_scroll()
        self._build_footer()
        self._cargar_todo()

    # ──────────────────────────────────────────────────────────────────────
    # Construcción de la UI
    # ──────────────────────────────────────────────────────────────────────
    def _build_header(self):
        from ui.components import boton_campana

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=16, pady=(18, 8))
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header,
            text="CONFIGURACIÓN",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=self.colors["text_primary"],
        ).grid(row=0, column=0, sticky="w")

        # Recargar + campana, juntos a la derecha
        acciones = ctk.CTkFrame(header, fg_color="transparent")
        acciones.grid(row=0, column=1, sticky="e")

        ctk.CTkButton(
            acciones,
            text="↺ Recargar",
            font=ctk.CTkFont(size=11),
            height=32,
            width=96,
            corner_radius=999,
            fg_color=self.colors["bg_card"],
            text_color=self.colors["text_muted"],
            hover_color=self.colors["border"],
            command=self._cargar_todo,
        ).pack(side="left", padx=(0, 8))

        boton_campana(
            acciones, self.colors, self.main_window.abrir_config_notificador
        ).pack(side="left")

    def _build_scroll(self):
        """Contenedor scrolleable donde vive todo el contenido dinámico."""
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
        footer.grid_columnconfigure(0, weight=1)

        ctk.CTkButton(
            footer,
            text="GUARDAR CAMBIOS",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=44,
            corner_radius=10,
            fg_color=self.colors["accent"],
            text_color="#ffffff",
            hover_color=self.colors["accent_hover"],
            command=self._guardar_todo,
        ).grid(row=0, column=0, sticky="ew")

    # ──────────────────────────────────────────────────────────────────────
    # Carga y renderizado
    # ──────────────────────────────────────────────────────────────────────
    def _cargar_todo(self):
        """Limpia y reconstruye todo el contenido del panel."""
        for widget in self.scroll.winfo_children():
            widget.destroy()
        self._widgets_global = {}
        self._widgets_bots = {}

        fila = 0
        fila = self._render_seccion_global(fila)
        fila = self._render_seccion_bots(fila)

    # ── Sección global ─────────────────────────────────────────────────────
    def _render_seccion_global(self, fila_inicial: int) -> int:
        """Config global (app / rutas) en una tarjeta con borde, estilo mockup."""
        config = leer_config_global()
        fila = fila_inicial

        # Juntamos app + rutas en una sola tarjeta "GENERAL"
        items = []
        for seccion in ("app", "rutas"):
            for clave, valor in config.get(seccion, {}).items():
                items.append((seccion, clave, valor))

        self._widgets_global = {"app": {}, "rutas": {}}

        tarjeta = self._tarjeta_seccion(fila, "GENERAL")
        fila += 1

        for i, (seccion, clave, valor) in enumerate(items):
            widget = self._render_fila_valor(
                tarjeta, i, clave, valor,
                _LABELS_GLOBAL.get(clave, clave),
                es_ultima=(i == len(items) - 1),
            )
            self._widgets_global[seccion][clave] = widget

        return fila

    # ── Sección por bot ─────────────────────────────────────────────────────
    def _render_seccion_bots(self, fila_inicial: int) -> int:
        """
        Config propia de cada bot.
        - 0 bots con config → nada.
        - 1 bot  → una tarjeta con su nombre.
        - +1 bots → pestañas (CTkTabview), una por bot, dentro de una tarjeta.
        """
        bots = leer_bots()
        bots_con_config = [b for b in bots if b.get("config")]

        if not bots_con_config:
            return fila_inicial

        fila = fila_inicial

        if len(bots_con_config) == 1:
            bot = bots_con_config[0]
            self._widgets_bots[bot["nombre"]] = {}

            tarjeta = self._tarjeta_seccion(fila, bot["nombre"].upper())
            fila += 1

            items = list(bot["config"].items())
            for i, (clave, valor) in enumerate(items):
                widget = self._render_fila_valor(
                    tarjeta, i, clave, valor, clave,
                    es_ultima=(i == len(items) - 1),
                )
                self._widgets_bots[bot["nombre"]][clave] = widget
        else:
            # Varios bots: pestañas dentro de una tarjeta
            tabview = ctk.CTkTabview(
                self.scroll,
                fg_color=self.colors["bg_card"],
                border_width=1,
                border_color=self.colors["border"],
                corner_radius=12,
                segmented_button_fg_color=self.colors["bg_inset"],
                segmented_button_selected_color=self.colors["accent"],
                segmented_button_selected_hover_color=self.colors["accent_hover"],
                segmented_button_unselected_color=self.colors["bg_inset"],
                text_color=self.colors["text_primary"],
            )
            tabview.grid(row=fila, column=0, sticky="ew", pady=(10, 4))
            fila += 1

            for bot in bots_con_config:
                nombre = bot["nombre"]
                tab = tabview.add(nombre)
                tab.grid_columnconfigure(0, weight=1)
                self._widgets_bots[nombre] = {}

                items = list(bot["config"].items())
                for i, (clave, valor) in enumerate(items):
                    widget = self._render_fila_valor(
                        tab, i, clave, valor, clave,
                        es_ultima=(i == len(items) - 1),
                    )
                    self._widgets_bots[nombre][clave] = widget

        return fila

    # ── Helpers de render ───────────────────────────────────────────────────
    def _tarjeta_seccion(self, fila: int, titulo: str):
        """
        Crea una tarjeta con borde y un título arriba, y devuelve el frame
        interno donde se agregan las filas de valores.
        """
        wrapper = ctk.CTkFrame(
            self.scroll,
            fg_color=self.colors["bg_card"],
            corner_radius=12,
            border_width=1,
            border_color=self.colors["border"],
        )
        wrapper.grid(row=fila, column=0, sticky="ew", pady=(10, 4))
        wrapper.grid_columnconfigure(0, weight=1)

        # Título de la tarjeta
        ctk.CTkLabel(
            wrapper,
            text=titulo,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.colors["accent_light"],
            anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(12, 4))

        # Frame interno para las filas
        interno = ctk.CTkFrame(wrapper, fg_color="transparent")
        interno.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 8))
        interno.grid_columnconfigure(0, weight=1)
        return interno

    def _render_fila_valor(self, parent, fila: int, clave: str, valor, label: str,
                           es_ultima: bool = False):
        """
        Fila estilo mockup: etiqueta a la izquierda, valor editable a la
        derecha (alineado a la derecha, sin recuadro en reposo), y una
        línea divisoria debajo (salvo la última).

        Devuelve el control (CTkEntry o BooleanVar) para leerlo al guardar.
        """
        fila_frame = ctk.CTkFrame(parent, fg_color="transparent")
        fila_frame.grid(row=fila * 2, column=0, sticky="ew", pady=2)
        fila_frame.grid_columnconfigure(1, weight=1)

        # Etiqueta a la izquierda
        ctk.CTkLabel(
            fila_frame,
            text=label,
            font=ctk.CTkFont(size=12),
            text_color=self.colors["text_muted"],
            width=150,
            anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=(8, 8), pady=8)

        if isinstance(valor, bool):
            var = ctk.BooleanVar(value=valor)
            ctk.CTkSwitch(
                fila_frame,
                text="",
                variable=var,
                width=44,
                button_color=self.colors["accent"],
                button_hover_color=self.colors["accent_hover"],
                progress_color=self.colors["accent"],
            ).grid(row=0, column=1, sticky="e", padx=(0, 8))
            control = var
        else:
            # Entry 
            entry = ctk.CTkEntry(
                fila_frame,
                height=30,
                corner_radius=6,
                fg_color=self.colors["bg_app"],
                border_width=0,
                text_color=self.colors["text_primary"],
                font=ctk.CTkFont(size=12),
                justify="right",
            )
            entry.insert(0, "" if valor is None else str(valor))
            entry.grid(row=0, column=1, sticky="ew", padx=(0, 8))
            
            control = entry

        # Línea divisoria (no en la última fila)
        if not es_ultima:
            ctk.CTkFrame(
                parent, height=1, fg_color=self.colors["border"],
            ).grid(row=fila * 2 + 1, column=0, sticky="ew", padx=8)

        return control

    # ──────────────────────────────────────────────────────────────────────
    # Guardado
    # ──────────────────────────────────────────────────────────────────────
    def _leer_widget(self, widget, valor_original):
        """
        Devuelve el valor actual de un widget, respetando el tipo original:
          - BooleanVar → bool
          - Entry sobre un int → int (si se puede convertir)
          - Entry → str
        """
        if isinstance(widget, ctk.BooleanVar):
            return widget.get()

        texto = widget.get().strip()
        # Si el valor original era int, intentamos preservar el tipo
        if isinstance(valor_original, int) and not isinstance(valor_original, bool):
            try:
                return int(texto)
            except ValueError:
                return texto
        return texto

    def _guardar_todo(self):
        """Guarda tanto la config global como la de cada bot."""
        ok_global = self._guardar_global()
        ok_bots = self._guardar_bots()

        if ok_global and ok_bots:
            self.main_window.set_status(
                "● Configuración guardada", self.colors["log_ok"],
            )
            self.after(2000, lambda: self.main_window.set_status("● En espera"))
        else:
            messagebox.showerror(
                "Error al guardar",
                "No se pudo guardar en settings.json.\n"
                "Verificá los permisos del archivo."
            )

    def _guardar_global(self) -> bool:
        original = leer_config_global()

        # Partimos de la config original para NO pisar secciones que este panel
        # ya no edita (SMTP se maneja en la ventana del notificador).
        nueva = {
            "app":   dict(original.get("app", {})),
            "smtp":  dict(original.get("smtp", {})),
            "rutas": dict(original.get("rutas", {})),
        }

        # Sobrescribimos solo lo que efectivamente se muestra en el panel
        for seccion, widgets in self._widgets_global.items():
            for clave, widget in widgets.items():
                valor_original = original.get(seccion, {}).get(clave)
                nueva[seccion][clave] = self._leer_widget(widget, valor_original)

        return guardar_config_global(nueva)

    def _guardar_bots(self) -> bool:
        """Guarda el bloque config de cada bot que se haya editado."""
        bots = {b["nombre"]: b for b in leer_bots()}
        ok = True

        for nombre, widgets in self._widgets_bots.items():
            config_original = bots.get(nombre, {}).get("config", {})
            nueva_config = {}
            for clave, widget in widgets.items():
                valor_original = config_original.get(clave)
                nueva_config[clave] = self._leer_widget(widget, valor_original)

            if not guardar_config_de_bot(nombre, nueva_config):
                ok = False

        return ok