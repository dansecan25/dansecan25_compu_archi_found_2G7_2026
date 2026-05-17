import tkinter as tk
from tkinter import messagebox
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

back = "#1A1A1A"


def button_hover(button, on_hover, on_leave):
    button.bind("<Enter>", func=lambda e: button.config(background=on_hover))

    button.bind("<Leave>", func=lambda e: button.config(background=on_leave))


class MainMenu:

    def __init__(self):
        self.master = tk.Tk()
        self.master.title("Ripes")
        self.master.resizable(False, False)
        self.master.config(bg=back)
        self.lftPos = (self.master.winfo_screenwidth() - 1500) / 2
        self.topPos = (self.master.winfo_screenheight() - 900) / 2
        self.master.geometry("%dx%d+%d+%d" % (1500, 900, self.lftPos, self.topPos))

        self.var = tk.StringVar()
        self.list = []
        self.filtered_list = []

        # Botones de la GUI

        self.edit_button = tk.Button(self.master, text="Editor", font=("Terminal", 20), width=10, height=2,
                                     pady=25,command=lambda: (), state=tk.DISABLED,
                                     bg="#3A3A3A", activebackground=back)
        self.process_button = tk.Button(self.master, text="Processor", font=("Terminal", 20), width=10, height=2,
                                        pady=25, command=lambda: self.processor_window(), activebackground=back)
        self.cache_button = tk.Button(self.master, text="Cache", font=("Terminal", 20), width=10, height=2, pady=25)

        self.edit_button.grid(column=0, row=0)
        self.process_button.grid(column=0, row=1)
        self.cache_button.grid(column=0, row=2)

        button_hover(self.process_button, "#3A3A3A", "SystemButtonFace")
        button_hover(self.cache_button, "#3A3A3A", "SystemButtonFace")

        # Editor
        self.editor_tab = tk.Frame(self.master, bg=back, width=645, height=525)
        self.editor_tab.grid_propagate(False)
        self.editor_tab.grid(column=1, row=0, sticky="nsew", rowspan=30)

        self.code_entry = tk.Text(self.editor_tab, height=30, width=80)
        self.reset_button = tk.Button(self.editor_tab, text="Reset", font=("Terminal", 20))
        self.step_back_button = tk.Button(self.editor_tab, text="<", font=("Terminal", 20))
        self.step_button = tk.Button(self.editor_tab, text=">", font=("Terminal", 20))
        self.run_button = tk.Button(self.editor_tab, text="Run", font=("Terminal", 20),
                                     command=lambda: self.get_txt())
        self.fast_button = tk.Button(self.editor_tab, text=">>", font=("Terminal", 20))


        self.reset_button.grid(column=1, row=0)
        self.step_back_button.grid(column=2, row=0)
        self.step_button.grid(column=3, row=0)
        self.run_button.grid(column=4, row=0)
        self.fast_button.grid(column=5, row=0)
        self.code_entry.grid(column=1, row=3, columnspan=5)
        self.edit_button.grid(column=0, row=0)

        # Processor
        #here will go processor tab

        # Path to log file
        self.log_path = os.path.join(os.path.dirname(__file__), "..", "log.txt")

        # Create processor view widget
        
    def processor_window(self):
        self.editor_tab.grid_forget()
        self.process_button.unbind("<Enter>")
        self.process_button.unbind("<Leave>")
        self.process_button.config(state=tk.DISABLED)
        button_hover(self.edit_button, "#3A3A3A", "SystemButtonFace")
        self.edit_button.config(state=tk.NORMAL, bg="SystemButtonFace")
        self.master.focus_set()
       
        



    def start(self):
        self.master.mainloop()


