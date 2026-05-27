import tkinter as tk
from tkinter import messagebox
import os, sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Pipeline view (ya existente)
from Front.processor_view import ProcessorView

# Nuevas vistas para Uniciclo y Multiciclo
from Front.vista_uniciclo   import VistaUniciclo
from Front.vista_multiciclo import VistaMulticiclo


class ProcessorWindow:

    def __init__(self, root, back, title, window_width, window_height, cpu):
        self.root = root
        self.back = back
        self.process_win = tk.Toplevel(self.root)
        self.process_win.title(title)
        self.process_win.resizable(True, True)
        self.process_win.config(bg=back)

        screen_width  = self.process_win.winfo_screenwidth()
        screen_height = self.process_win.winfo_screenheight()

        max_width  = int(screen_width  * 0.72)
        max_height = int(screen_height * 0.80)

        # Uniciclo / Multiciclo necesitan más espacio horizontal
        if cpu in [0, 1]:
            actual_width  = min(window_width,  max_width,  1120)
            actual_height = min(window_height, max_height, 640)
            self.lftPos   = 40
        else:
            actual_width  = min(window_width,  max_width,  1100)
            actual_height = min(window_height, max_height, 700)
            self.lftPos   = screen_width - actual_width - 40

        self.topPos = max(40, (screen_height - actual_height) // 2)
        self.process_win.geometry(
            "%dx%d+%d+%d" % (actual_width, actual_height, self.lftPos, self.topPos))

        self.processor_tab = tk.Frame(self.process_win, bg="#1A1A1A")
        self.processor_tab.pack(fill='both', expand=True)

        self.log_files = [
            "log_uniciclo.txt",                   # 0: CPU Uniciclo
            "log_multiciclo.txt",                 # 1: CPU Multiciclo
            "log.txt",                            # 2: Pipeline sin Hazards
            "log_hazard_control.txt",             # 3: Pipeline con Hazard Control
            "log_prediccion.txt",                 # 4: Pipeline con Predicción
            "log_prediccion_hazard_control.txt",  # 5: Pipeline Predicción + HC
        ]

        self.log_path = os.path.join(os.path.dirname(__file__), self.log_files[cpu])

        if cpu == 0:           # Uniciclo
            self.vista = VistaUniciclo(self.processor_tab, self.log_path)
            self.vista.pack(fill='both', expand=True)

        elif cpu == 1:         # Multiciclo
            self.vista = VistaMulticiclo(self.processor_tab, self.log_path)
            self.vista.pack(fill='both', expand=True)

        else:                  # Pipeline (2-5)
            self.processor_view = ProcessorView(self.processor_tab, self.log_path)
            self.processor_view.pack(fill='both', expand=True)
            if self.processor_view:
                success = self.processor_view.load_log()
                if not success:
                    messagebox.showerror(
                        "Error",
                        f"Failed to load simulation log: {self.log_files[cpu]}")

        self.process_win.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        self.process_win.destroy()
