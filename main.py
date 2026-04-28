import customtkinter as ctk
from ui.main_window import MainWindow

# ─── Tema global ───
# customtkinter maneja temas "dark" / "light" / "system".
ctk.set_appearance_mode("dark")

# El color de acento que usa customtkinter para botones, toggles, etc.
ctk.set_default_color_theme("blue")


def main():
    # Creamos la ventana raíz usando CTk (la versión moderna de Tk)
    app = MainWindow()

    # Centramos la ventana en pantalla antes de mostrarla
    app.center_window()

    # Arranca el loop principal de la UI (equivalente al mainloop() de tkinter)
    app.mainloop()


if __name__ == "__main__":
    main()