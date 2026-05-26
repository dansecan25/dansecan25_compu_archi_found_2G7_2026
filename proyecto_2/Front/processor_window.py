import tkinter as tk
from tkinter import messagebox
import os, sys
from Front.processor_view import ProcessorView
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))




class ProcessorWindow:


    def __init__(self, root, back, title, window_width, window_height, cpu):
        self.root = root
        self.back = back
        self.process_win = tk.Toplevel(self.root)
        self.process_win.title(title)
        self.process_win.resizable(True, True)  # Permitir redimensionar
        self.process_win.config(bg=back)
        
        # Obtener dimensiones de pantalla
        screen_width = self.process_win.winfo_screenwidth()
        screen_height = self.process_win.winfo_screenheight()
        
        # Ajustar tamaño de ventana (máximo 70% de pantalla)
        max_width = int(screen_width * 0.7)
        max_height = int(screen_height * 0.75)
        actual_width = min(window_width, max_width, 1100)
        actual_height = min(window_height, max_height, 700)
        
        # Posicionar ventanas lado a lado
        # CPU 0 y 1 (primera columna) van a la izquierda
        # CPU 2 y 3 (segunda columna) van a la derecha
        if cpu in [0, 1]:
            # Ventana izquierda
            self.lftPos = 50
        else:
            # Ventana derecha
            self.lftPos = screen_width - actual_width - 50
        
        # Posición vertical centrada pero visible
        self.topPos = max(50, (screen_height - actual_height) / 2)
        
        self.process_win.geometry("%dx%d+%d+%d" % (actual_width, actual_height, self.lftPos, self.topPos))

        self.processor_tab = tk.Frame(self.process_win, bg="#1A1A1A")
        self.processor_tab.pack(fill='both', expand=True)

        self.log_files = ["log.txt", "log_prediccion.txt", "log_hazard_control.txt", "log_prediccion_hazard_control.txt"]

        # Path to log file
        self.log_path = os.path.join(os.path.dirname(__file__), self.log_files[cpu])

        # Create processor view widget
        self.processor_view = ProcessorView(self.processor_tab, self.log_path)
        self.processor_view.pack(fill='both', expand=True)

        if self.processor_view:
           success = self.processor_view.load_log()
           if not success:
               messagebox.showerror("Error", f"Failed to load simulation log: {self.log_files[cpu]}")

        self.process_win.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        self.process_win.destroy()
        self.process_win.destroy()

