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
from Config.settings import *


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

        self.colors = colors
        self.main_window = main_window

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Lista de CTkEntry 
        self._widget_global ={}
        self._widgets_bot ={}

        self._build_header()
        self._build_scroll()
        self._build_footer()
        self._cargar_todo()



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
            command=self._cargar_todo,
        ).pack(side="right")


    def _build_scroll(self):
        """
        Contenedor del scroll donde esta el contenido dinamico
        """
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
            text="Guardar cambios",
            font=ctk.CTkFont(size=14),
            height=38,
            corner_radius=12,
            fg_color=self.colors["accent"],
            hover_color="#1560a0",
            command=self._guardar_todo,
        ).grid(row=0, column=0, sticky="ew")



    # Carga y renderizado
    def _cargar_todo(self):
        """Limpia y reconstruye el contenido del panel"""
        for widget in self.scroll.winfo_children():
            widget.destroy()
        self._widgets_global = {}
        self._widgets_bot = {}

        fila = 0
        fila = self._render_seccion_global(fila)
        fila = self._render_seccion_bot(fila)


    # Seccion global 
    def _render_seccion_global(self, fila_inicial:int) -> int:
        """
        Renderiza las secciones app, smtp, rutas
        """
        config = leer_config_global()
        fila = fila_inicial
       
        self._titulo_seccion("General", fila)
        fila += 1
        
        secciones =[
            ("app", config.get("app",{})),
            ("smtp", config.get("smtp",{})),
            ("rutas", config.get("rutas",{})),
        ]
        
        for nombre_seccion, valores in secciones:
            self._widget_global[nombre_seccion] = {}
            for clave, valor in valores.items():
                widget = self._render_fila_valor(
                    self.scroll, fila, clave, valor, _LABELS_GLOBAL.get(clave, clave)
                )
                self._widget_global[nombre_seccion][clave] = widget
                fila += 1
        
        return fila

    #Seccion por bot
    def _render_seccion_bot(self, fila_inicial:int) -> int:
        """
        Renderiza la config para cada bot.
        si tiene 1 bot muestra sus variables, y si tiene mas de uno aparecen en pesatañas
        """
        bots = leer_bots()
        #Solo se considera bots q tengan al menos una variable
        bots_con_config = [b for b in bots if b.get("config")]

        if not bots_con_config:
            return fila_inicial
        
        fila = fila_inicial
        
        ctk.CTkFrame(
            self.scroll, height=1, fg_color=self.colors["border"],
        ).grid(row=fila, column=0, sticky="ew", pady=(16, 4))
        fila += 1
 
        self._titulo_seccion("Variables por bot", fila)
        fila += 1
 
        if len(bots_con_config) == 1:
            # Un solo bot, sus variables directas, sin pestañas
            bot = bots_con_config[0]
            self._widgets_bot[bot["nombre"]] = {}
 
            ctk.CTkLabel(
                self.scroll,
                text=bot["nombre"],
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=self.colors["accent_light"],
                anchor="w",
            ).grid(row=fila, column=0, sticky="w", padx=4, pady=(4, 2))
            fila += 1
 
            for clave, valor in bot["config"].items():
                widget = self._render_fila_valor(self.scroll, fila, clave, valor, clave)
                self._widgets_bot[bot["nombre"]][clave] = widget
                fila += 1
        else:
            # Varios bots, pestañas
            tabview = ctk.CTkTabview(
                self.scroll,
                fg_color=self.colors["bg_card"],
                segmented_button_fg_color=self.colors["bg_sidebar"],
                segmented_button_selected_color=self.colors["accent"],
                segmented_button_selected_hover_color="#1560a0",
                segmented_button_unselected_color=self.colors["bg_sidebar"],
                text_color=self.colors["text_primary"],
            )
            tabview.grid(row=fila, column=0, sticky="ew", pady=4)
            fila += 1
 
            for bot in bots_con_config:
                nombre = bot["nombre"]
                tab = tabview.add(nombre)
                tab.grid_columnconfigure(0, weight=1)
                self._widgets_bot[nombre] = {}
 
                for i, (clave, valor) in enumerate(bot["config"].items()):
                    widget = self._render_fila_valor(tab, i, clave, valor, clave)
                    self._widgets_bot[nombre][clave] = widget
 
        return fila
        
        
        
    def _titulo_seccion(self, texto: str, fila: int):
        ctk.CTkLabel(
            self.scroll,
            text=texto.upper(),
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.colors["accent_light"],
            anchor="w",
        ).grid(row=fila, column=0, sticky="w", padx=4, pady=(8, 4))
 
    def _render_fila_valor(self, parent, fila: int, clave: str, valor, label: str):
        """
        Renderiza una fila 'etiqueta + control' y devuelve el control
        (CTkEntry o BooleanVar) para poder leerlo después.
 
        - bool → switch
        - resto → entry de texto
        """
        contenedor = ctk.CTkFrame(parent, fg_color="transparent")
        contenedor.grid(row=fila, column=0, sticky="ew", pady=3)
        contenedor.grid_columnconfigure(1, weight=1)
 
        ctk.CTkLabel(
            contenedor,
            text=label,
            font=ctk.CTkFont(size=12),
            text_color=self.colors["text_muted"],
            anchor="w",
            width=150,
        ).grid(row=0, column=0, sticky="w", padx=(4, 8))
 
        if isinstance(valor, bool):
            var = ctk.BooleanVar(value=valor)
            ctk.CTkSwitch(
                contenedor,
                text="",
                variable=var,
                width=44,
                button_color=self.colors["accent"],
                button_hover_color="#1560a0",
                progress_color=self.colors["accent"],
            ).grid(row=0, column=1, sticky="w")
            return var
 
        entry = ctk.CTkEntry(
            contenedor,
            height=30,
            corner_radius=6,
            fg_color=self.colors["bg_app"],
            border_color=self.colors["border"],
            text_color=self.colors["text_primary"],
            font=ctk.CTkFont(size=12),
        )
        entry.insert(0, "" if valor is None else str(valor))
        entry.grid(row=0, column=1, sticky="ew")
        return entry
 
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
        nueva = {"app": {}, "smtp": {}, "rutas": {}}
 
        for seccion, widgets in self._widgets_global.items():
            for clave, widget in widgets.items():
                valor_original = original.get(seccion, {}).get(clave)
                nueva[seccion][clave] = self._leer_widget(widget, valor_original)
 
        return guardar_config_global(nueva)
 
    def _guardar_bots(self) -> bool:
        """Guarda el bloque config de cada bot que se haya editado."""
        bots = {b["nombre"]: b for b in leer_bots()}
        ok = True
 
        for nombre, widgets in self._widgets_bot.items():
            config_original = bots.get(nombre, {}).get("config", {})
            nueva_config = {}
            for clave, widget in widgets.items():
                valor_original = config_original.get(clave)
                nueva_config[clave] = self._leer_widget(widget, valor_original)
 
            if not guardar_config_de_bot(nombre, nueva_config):
                ok = False
 
        return ok