import customtkinter as ctk


def boton_campana(parent, colors: dict, command):
    """
    Botón de campana para abrir la configuración del notificador.
    Se ubica en el header de los paneles, alineado a la derecha.
    """
    
    return ctk.CTkButton(
        parent,
        text="🔔",
        width=40,
        height=40,
        corner_radius=10,
        font=ctk.CTkFont(size=16),
        fg_color=colors["bg_card"],
        text_color=colors["text_primary"],
        border_width=1,
        border_color=colors["border"],
        command=command,
    )


def titulo_panel(parent, colors: dict, texto: str):
    """
    Título grande de panel, en mayúsculas y bold (estilo de encabezado
    de sección). Devuelve el label por si se quiere ajustar luego.
    """
    return ctk.CTkLabel(
        parent,
        text=texto.upper(),
        font=ctk.CTkFont(size=18, weight="bold"),
        text_color=colors["text_primary"],
    )