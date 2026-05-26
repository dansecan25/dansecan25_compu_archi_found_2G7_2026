import tkinter as tk
from tkinter import messagebox
import os, sys
from Front.processor_view import ProcessorView
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))




class ProcessorWindow:


    def __init__(self, root, back, title, lft_pos, top_pos, cpu):
        self.root = root
        self.back = back
        self.process_win  = tk.Toplevel(self.root)
        self.process_win.title(title)
        self.process_win.resizable(False, False)
        self.process_win.config(bg=back)
        self.lftPos = (self.process_win.winfo_screenwidth() - lft_pos) / 2
        self.topPos = (self.process_win.winfo_screenheight() - top_pos) / 2
        self.process_win.geometry("%dx%d+%d+%d" % (1250, 750, self.lftPos, self.topPos))

        self.processor_tab = tk.Frame(self.process_win, bg="#1A1A1A", width=1280, height=900)
        self.processor_tab.grid_propagate(False)

        self.log_files = ["log.txt", "log_prediccion.txt", "log_hazard_control.txt", "log_prediccion_hazard_control.txt"]

        # Path to log file
        self.log_path = os.path.join(os.path.dirname(__file__), self.log_files[cpu])

        # Create processor view widget
        self.processor_view = ProcessorView(self.processor_tab, self.log_path)
        self.processor_view.grid(column=1, row=0, sticky="nsew", rowspan=30)

        self.processor_tab.grid(column=1, row=0, sticky="nsew", rowspan=30)

        if self.processor_view:
           success = self.processor_view.load_log()
           #if success:
           #    messagebox.showinfo("Success", "Simulation completed! Switch to Processor tab to view pipeline execution.")
           #else:
           #    messagebox.showerror("Error", "Failed to load simulation log.")

        self.process_win.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        self.process_win.destroy()
        self.process_win.destroy()

