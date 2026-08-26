"""
ui/config_window.py

Ventana modal de configuración del notificador (mail).
Se abre desde el botón de campana en el header de los paneles.

Concentra la configuración SMTP editable por el usuario:
    - Usuario SMTP (remitente)
    - Contraseña / app password
    - Destinatarios
    - Interruptor de notificaciones

El host y el puerto NO se editan acá: son constantes de sistema y viven
en config/config_sistema.py.
"""

import customtkinter as ctk
from tkinter import messagebox
from config.almacenamiento import leer_config_global, guardar_config_global


class ConfigNotificadorWindow(ctk.CTkToplevel):

    def __init__(self, parent, colors: dict):
        super().__init__(parent)

        self.colors = colors

        self.title("Configuración del notificador")
        self.geometry("460x440")
        self.resizable(False, False)
        self.configure(fg_color=colors["bg_app"])
        self.transient(parent)
        self.grab_set()

        # Centramos respecto de la ventana padre
        self.after(10, self._centrar_sobre_padre, parent)

        self._entries = {}
        self._build()
        self._cargar()

    # ──────────────────────────────────────────────────────────────────────
    def _build(self):
        self.grid_columnconfigure(0, weight=1)

        # ── Encabezado ──
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(22, 4))

        ctk.CTkLabel(
            header,
            text="🔔  NOTIFICACIONES POR MAIL",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=self.colors["text_primary"],
        ).pack(side="left")

        ctk.CTkLabel(
            self,
            text="Reporte automático al terminar cada bot.",
            font=ctk.CTkFont(size=11),
            text_color=self.colors["text_muted"],
            anchor="w",
        ).grid(row=1, column=0, sticky="w", padx=24, pady=(0, 14))

        # ── Tarjeta con los campos ──
        card = ctk.CTkFrame(self, fg_color=self.colors["bg_card"], corner_radius=12)
        card.grid(row=2, column=0, sticky="ew", padx=24)
        card.grid_columnconfigure(0, weight=1)

        self._campo(card, "user",         "Usuario SMTP",   "ejemplo@gmail.com")
        self._campo(card, "pass",         "Contraseña",     "app password", show="•")
        self._campo(card, "mail_destino", "Destinatarios",  "separados por coma")

        # Toggle de activación
        fila_toggle = ctk.CTkFrame(card, fg_color="transparent")
        fila_toggle.grid(sticky="ew", padx=16, pady=(6, 14))
        fila_toggle.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            fila_toggle,
            text="Notificar por mail",
            font=ctk.CTkFont(size=12),
            text_color=self.colors["text_primary"],
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

        self._notif_var = ctk.BooleanVar(value=False)
        ctk.CTkSwitch(
            fila_toggle,
            text="",
            variable=self._notif_var,
            width=44,
            button_color=self.colors["accent"],
            button_hover_color=self.colors["accent_hover"],
            progress_color=self.colors["accent"],
        ).grid(row=0, column=1, sticky="e")

        # ── Botones ──
        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.grid(row=3, column=0, sticky="ew", padx=24, pady=(20, 20))
        btns.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(
            btns, text="Cancelar", height=40, corner_radius=10,
            fg_color=self.colors["bg_card"],
            text_color=self.colors["text_muted"],
            hover_color=self.colors["border"],
            border_width=1, border_color=self.colors["border"],
            command=self.destroy,
        ).grid(row=0, column=0, sticky="ew", padx=(0, 6))

        ctk.CTkButton(
            btns, text="GUARDAR", height=40, corner_radius=10,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=self.colors["accent"],
            hover_color=self.colors["accent_hover"],
            command=self._guardar,
        ).grid(row=0, column=1, sticky="ew", padx=(6, 0))

    def _campo(self, parent, clave, label, placeholder, show=None):
        cont = ctk.CTkFrame(parent, fg_color="transparent")
        cont.grid(sticky="ew", padx=16, pady=(14, 0))
        cont.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            cont, text=label,
            font=ctk.CTkFont(size=11),
            text_color=self.colors["text_muted"],
            anchor="w",
        ).grid(row=0, column=0, sticky="w", pady=(0, 4))

        entry = ctk.CTkEntry(
            cont, placeholder_text=placeholder,
            height=36, corner_radius=8,
            fg_color=self.colors["bg_inset"],
            border_color=self.colors["border"],
            text_color=self.colors["text_primary"],
        )
        if show:
            entry.configure(show=show)
        entry.grid(row=1, column=0, sticky="ew")
        self._entries[clave] = entry

    # ──────────────────────────────────────────────────────────────────────
    def _cargar(self):
        smtp = leer_config_global().get("smtp", {})
        for clave, entry in self._entries.items():
            entry.insert(0, str(smtp.get(clave, "") or ""))
        self._notif_var.set(bool(smtp.get("notif_mail", False)))

    def _guardar(self):
        config = leer_config_global()
        config.setdefault("smtp", {})
        for clave, entry in self._entries.items():
            config["smtp"][clave] = entry.get().strip()
        config["smtp"]["notif_mail"] = self._notif_var.get()

        if guardar_config_global(config):
            self.destroy()
        else:
            messagebox.showerror(
                "Error al guardar",
                "No se pudo guardar en settings.json.\n"
                "Verificá los permisos del archivo.",
            )

    def _centrar_sobre_padre(self, parent):
        try:
            self.update_idletasks()
            px, py = parent.winfo_rootx(), parent.winfo_rooty()
            pw, ph = parent.winfo_width(), parent.winfo_height()
            w, h = self.winfo_width(), self.winfo_height()
            x = px + (pw - w) // 2
            y = py + (ph - h) // 2
            self.geometry(f"+{x}+{y}")
        except Exception:
            pass