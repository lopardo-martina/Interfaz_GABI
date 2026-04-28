"""
ui/panels/panel_config.py

Panel de configuración. Lee la hoja 'Sheet1' del settings.xlsx
y muestra cada fila (CLAVE / VALOR / DETALLE) como una fila editable.

El usuario puede editar los valores directamente y guardar con el botón.
Las claves y los detalles son de solo lectura — solo el VALOR es editable.
"""

import customtkinter as ctk
from tkinter import messagebox
from core.excel_utils import leer_config, guardar_config


class PanelConfig(ctk.CTkFrame):

    def __init__(self, parent, colors: dict, main_window):
        super().__init__(parent, fg_color=colors["bg_panel"], corner_radius=0)

        self.colors      = colors
        self.main_window = main_window

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Lista de CTkEntry de valores — la llenamos al cargar
        self._entries_valor = []

        self._build_header()
        self._build_tabla()
        self._build_footer()
        self._cargar_config()



    # Construcción de la UI
    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=16, pady=6)

        ctk.CTkLabel(
            header,
            text="Configuración",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.colors["text_primary"],
        ).pack(side="left")

        # Botón para recargar desde el Excel (útil si se editó manualmente)
        ctk.CTkButton(
            header,
            text="↺ Recargar",
            font=ctk.CTkFont(size=11),
            height=28,
            width=90,
            corner_radius=999,
            fg_color=self.colors["bg_card"],
            text_color=self.colors["text_muted"],
            hover_color=self.colors["border"],
            command=self._cargar_config,
        ).pack(side="right")


    def _build_tabla(self):
        """
        Área scrolleable con las filas de configuración.
        Cada fila tiene: etiqueta CLAVE (readonly) | entry VALOR (editable) | texto DETALLE (readonly)
        """
        # Encabezados de columnas
        encabezados = ctk.CTkFrame(self, fg_color=self.colors["bg_card"], corner_radius=6)
        encabezados.grid(row=0, column=0, sticky="ew", padx=16, pady=(90, 0))
        encabezados.grid_columnconfigure(1, weight=1)

        for col, texto in enumerate(["CLAVE", "VALOR", "DETALLE"]):
            ctk.CTkLabel(
                encabezados,
                text=texto,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=self.colors["accent_light"],
                anchor="w",
            ).grid(row=0, column=col, sticky="w", padx=14, pady=6)

        encabezados.grid_columnconfigure(0, minsize=130)
        encabezados.grid_columnconfigure(1, weight=1)
        encabezados.grid_columnconfigure(2, minsize=180)

        # Área scrolleable para las filas
        self.scroll = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=self.colors["bg_card"],
            scrollbar_button_hover_color=self.colors["border"],
        )
        self.scroll.grid(row=1, column=0, sticky="nsew", padx=16, pady=(4, 4))
        self.scroll.grid_columnconfigure(0, weight=1)

    def _build_footer(self):
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.grid(row=2, column=0, sticky="ew", padx=16, pady=(4, 14))
        footer.grid_columnconfigure(0, weight=1)

        ctk.CTkButton(
            footer,
            text="Guardar cambios",
            font=ctk.CTkFont(size=14),
            height=38,
            corner_radius=12,
            fg_color=self.colors["accent"],
            hover_color="#1560a0",
            command=self._guardar_config,
        ).grid(row=0, column=0, sticky="ew")



    # Carga y renderizado
    def _cargar_config(self):
        """Lee el Excel y renderiza las filas."""
        for widget in self.scroll.winfo_children():
            widget.destroy()
        self._entries_valor = []

        config = leer_config()

        if not config:
            ctk.CTkLabel(
                self.scroll,
                text="No se encontró configuración en settings.xlsx.\n"
                     "Verificá que el archivo exista en la carpeta config/.",
                font=ctk.CTkFont(size=14),
                text_color=self.colors["text_muted"],
                justify="center",
            ).pack(expand=True, pady=40)
            return

        for i, item in enumerate(config):
            self._render_fila(i, item)

    def _render_fila(self, indice: int, item: dict):
        """
        Renderiza una fila de configuración.
        """
        # Alternar color de fondo para facilitar la lectura
        bg = self.colors["bg_card"] if indice % 2 == 0 else "#222226"

        fila = ctk.CTkFrame(
            self.scroll,
            fg_color=bg,
            corner_radius=6,
        )
        fila.grid(row=indice, column=0, sticky="ew", pady=2)
        fila.grid_columnconfigure(0, minsize=130)
        fila.grid_columnconfigure(1, weight=1)
        fila.grid_columnconfigure(2, minsize=180)

        # ── Clave (solo lectura) ─────
        ctk.CTkLabel(
            fila,
            text=item["clave"],
            font=ctk.CTkFont(size=12),
            text_color=self.colors["text_muted"],
            anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=(14, 5), pady=8)


        # ── Valor (editable) ──────
        entry = ctk.CTkEntry(
            fila,
            height=30,
            corner_radius=6,
            fg_color=self.colors["bg_app"],
            border_color=self.colors["border"],
            text_color=self.colors["text_primary"],
            font=ctk.CTkFont(size=12),
        )
        entry.insert(0, item["valor"])
        entry.grid(row=0, column=1, sticky="ew", padx=5, pady=6)
        self._entries_valor.append((item, entry))


        # ── Detalle (solo lectura, texto gris más pequeño) ────
        ctk.CTkLabel(
            fila,
            text=item["detalle"],
            font=ctk.CTkFont(size=11),
            text_color=self.colors["text_dim"],
            anchor="w",
            wraplength=180,   # envuelve si es muy largo
        ).grid(row=0, column=2, sticky="w", padx=5, pady=8)



    # Acciones
    def _guardar_config(self):
        """Lee los valores actuales de los entries y guarda en el Excel."""
        config_actualizada = []

        for item, entry in self._entries_valor:
            config_actualizada.append({
                "clave":   item["clave"],
                "valor":   entry.get().strip(),
                "detalle": item["detalle"],
            })

        ok = guardar_config(config_actualizada)

        if ok:
            self.main_window.set_status(
                "● Configuración guardada",
                self.colors["log_ok"],
            )
            self.after(2000, lambda: self.main_window.set_status("● En espera"))
        else:
            messagebox.showerror(
                "Error al guardar",
                "No se pudo guardar en settings.xlsx.\n"
                "Verificá que el archivo no esté abierto en Excel."
            )