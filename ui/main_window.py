import os
import customtkinter as ctk
from ui.panels.panel_main   import PanelMain
from ui.panels.panel_bots   import PanelBots
from ui.panels.panel_config import PanelConfig

# ─── Paleta de colores ──
# Definimos los colores acá para que todos los paneles puedan importarlos
# desde un único lugar. Si querés cambiar un color, lo cambiás una sola vez.
COLORS = {
    "bg_app":        "#1e1e20",   # fondo general
    "bg_sidebar":    "#101011",   # sidebar más oscuro
    "bg_panel":      "#1e1e20",   # fondo de los paneles
    "bg_card":       "#26262a",   # tarjetas / filas
    
    "border":        "#43454D",   # líneas divisorias
    
    "logo_fondo":    "#c4d6e0",
    
    "accent":        "#1a6fb5",   # azul principal (botones, activo)
    "accent_light":  "#9ed3f5",   # celeste para texto sobre azul
    "accent_dark":   "#1a3a5c",   # azul mas oscuro (hover, botón activo)
    
    "text_primary":  "#e0e0e0",   # texto principal
    "text_muted":    "#888888",   # texto secundario
    "text_dim":      "#555555",   # texto muy apagado
    
    "log_info":      "#7ec8f7",   # líneas info en el log
    "log_ok":        "#62af7b",   # líneas ok/verde en el log
    "log_warn":      "#f5ba31",   # líneas advertencia
    "log_error":     "#f58e8e",   # líneas error
    
    "danger":        "#6b3333",   # fondo botón detener
    "danger_text":   "#f16e6e",   # texto botón detener
}


class MainWindow(ctk.CTk):
    """
    Ventana raíz de GABI. Contiene el layout base con el sidebar y el área de contenido.
    """

    WIDTH  = 820
    HEIGHT = 540

    def __init__(self):
        super().__init__()

        self.title("GABI")
        self.geometry(f"{self.WIDTH}x{self.HEIGHT}")
        self.resizable(False, False)  # ventana fija

        # Color de fondo de la ventana raíz
        self.configure(fg_color=COLORS["bg_app"])

        # Se intenta cargar el ícono si existe, sino lo ignora
        try:
            self.iconbitmap("statics/icono_mini.ico")
        except Exception:
            pass  

        self._build_layout()
        self._build_sidebar()
        self._build_content_area()

        # Se muestra el panel principal al arrancar
        self._show_panel("main")




    """Layout base"""
    def _build_layout(self):
        """Crea las dos columnas: sidebar (fija) y contenido (expandible)."""

        # Columna 0 = sidebar: ancho fijo de 150px
        # Columna 1 = contenido: ocupa todo el espacio restante
        self.grid_columnconfigure(0, weight=0, minsize=150)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)




    """Sidebar"""
    def _build_sidebar(self):
        """Construye el sidebar: logo + navegación + estado."""

        # Marco contenedor del sidebar
        self.sidebar = ctk.CTkFrame(
            self,
            fg_color=COLORS["bg_sidebar"],
            corner_radius=0,
            border_width=0,
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(1, weight=1)  # la nav se expande

        # ── Logo ────
        logo_frame = ctk.CTkFrame(
            self.sidebar,
            fg_color="transparent",
            corner_radius=0,
        )
        logo_frame.grid(row=0, column=0, sticky="ew", padx=16, pady=(18, 12))
 
        # Logo desde archivo de imagen
        # Si no existe el archivo, cae al texto de fallback
        try:
            from PIL import Image
            img_logo = Image.open(os.path.join("Statics", "logo.png"))
            img_logo = img_logo.resize((200, 280), Image.Resampling.LANCZOS)
            logo_ctk = ctk.CTkImage(light_image=img_logo, dark_image=img_logo, size=(210, 170))
            ctk.CTkLabel(
                logo_frame,
                image=logo_ctk,
                text="",
                width=210,
                height=170,
            ).pack(side="left")
        except Exception:
            # Texto si no se encuentra la imagen
            ctk.CTkLabel(
                logo_frame,
                text="GABI",
                font=ctk.CTkFont(size=15, weight="bold"),
                text_color=COLORS["text_primary"],
            ).pack(side="left")
 
 
        # Línea divisora debajo del logo
        ctk.CTkFrame(
            self.sidebar,
            height=1,
            fg_color=COLORS["border"],
        ).grid(row=0, column=0, sticky="sew", pady=(0, 0))



        # ── Navegación ───
        # Se guardan los botones en un dict para poder cambiar su estilo, cuando el panel activo cambia.
        nav_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        nav_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

        self._nav_buttons = {}

        nav_items = [
            ("main",   "≡  Principal"),
            ("bots",   "≡  Bots"),
            ("config", "⚙  Configuración"),
        ]

        for panel_name, label in nav_items:
            btn = ctk.CTkButton(
                nav_frame,
                text=label,
                font=ctk.CTkFont(size=14),
                anchor="w",
                height=38,
                corner_radius=10,
                fg_color="transparent",
                text_color=COLORS["text_muted"],
                hover_color="#26262a",
                command=lambda p=panel_name: self._show_panel(p),
            )
            btn.pack(fill="x", pady=2)
            self._nav_buttons[panel_name] = btn

        # ── Footer del sidebar: estado del sistema ──────
        footer = ctk.CTkFrame(
            self.sidebar,
            fg_color="transparent",
            corner_radius=0,
        )
        footer.grid(row=2, column=0, sticky="sew", padx=12, pady=(0, 12))

        # Línea divisora sobre el footer
        ctk.CTkFrame(
            self.sidebar,
            height=1,
            fg_color=COLORS["border"],
        ).grid(row=2, column=0, sticky="new")

        # Label de estado — se guarda para actualizarse desde los paneles
        self.status_label = ctk.CTkLabel(
            footer,
            text="● En espera",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_dim"],
        )
        self.status_label.pack(anchor="w", pady=(12, 0))


    """Área de contenido"""
    def _build_content_area(self):
        """
        Crea el contenedor derecho y carga los tres paneles.
        Solo uno estará visible a la vez; los demás quedan ocultos con grid_remove().
        """
        self.content = ctk.CTkFrame(
            self,
            fg_color=COLORS["bg_panel"],
            corner_radius=0,
        )
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

        # Instanciamos los tres paneles. Cada uno recibe:
        #   - parent: el contenedor donde se dibuja
        #   - colors: la paleta compartida
        #   - main_window: referencia a esta ventana (para actualizar el status)
        self._panels = {
            "main":   PanelMain(self.content,   COLORS, self),
            "bots":   PanelBots(self.content,   COLORS, self),
            "config": PanelConfig(self.content, COLORS, self),
        }

        # Todos los paneles ocupan la misma celda del grid (row=0, col=0).
        # Usamos grid_remove() para ocultar los que no están activos.
        for panel in self._panels.values():
            panel.grid(row=0, column=0, sticky="nsew")
            panel.grid_remove()


    """Navegación"""
    def _show_panel(self, name: str):
        """
        Muestra el panel indicado y oculta los demás.
        También actualiza el estilo del botón activo en el sidebar.
        """
        # Ocultar todos los paneles
        for panel in self._panels.values():
            panel.grid_remove()

        # Mostrar el panel pedido
        self._panels[name].grid()

        # Actualizar estilos de los botones de navegación
        for btn_name, btn in self._nav_buttons.items():
            if btn_name == name:  #btn activo
                btn.configure(
                    fg_color=COLORS["accent_dark"],
                    text_color=COLORS["accent_light"],
                )
            else: #btn inactivo
                btn.configure(
                    fg_color="transparent",
                    text_color=COLORS["text_muted"],
                )

    
    """Métodos públicos (usados por los paneles)  """
    def set_status(self, text: str, color: str = None):
        """
        Actualiza el texto de estado en el footer del sidebar.
        Los paneles llaman a esto cuando cambia el estado de ejecución.
        """
        self.status_label.configure(
            text=text,
            text_color=color or COLORS["text_dim"],
        )

    def center_window(self):
        """Centra la ventana en la pantalla antes de mostrarla."""
        self.update_idletasks()
        #screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = 20
        y = ((screen_h - self.HEIGHT) // 2) + 20
        self.geometry(f"{self.WIDTH}x{self.HEIGHT}+{x}+{y}")