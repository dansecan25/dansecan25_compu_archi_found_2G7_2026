import tkinter as tk
import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from processor_view import ProcessorView


class ProcessorWindow:
    """Ventana Toplevel que contiene la vista del pipeline."""

    def __init__(self, root, back, title, lft_pos, top_pos, log_path):
        self.root = root
        self.back = back
        self.log_path = log_path

        self.process_win = tk.Toplevel(self.root)
        self.process_win.title(title)
        self.process_win.resizable(False, False)
        self.process_win.config(bg=back)
        self.lftPos = (self.process_win.winfo_screenwidth() - lft_pos) / 2
        self.topPos = (self.process_win.winfo_screenheight() - top_pos) / 2
        self.process_win.geometry("%dx%d+%d+%d" % (1250, 750, self.lftPos, self.topPos))

        self.processor_tab = tk.Frame(self.process_win, bg="#1A1A1A", width=1280, height=900)
        self.processor_tab.grid_propagate(False)

        # Crear el widget de vista del procesador
        self.processor_view = ProcessorView(self.processor_tab, self.log_path)
        self.processor_view.grid(column=1, row=0, sticky="nsew", rowspan=30)

        self.processor_tab.grid(column=1, row=0, sticky="nsew", rowspan=30)

        if self.processor_view:
            self.processor_view.load_log()

        self.process_win.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        self.process_win.destroy()
