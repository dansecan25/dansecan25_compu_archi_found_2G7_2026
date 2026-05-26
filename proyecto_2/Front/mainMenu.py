import tkinter as tk
from tkinter import messagebox, ttk
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Front.processor_window import ProcessorWindow
from Front.simulator_runner import SimulatorRunner
from processor_view import ProcessorView

back = "#1A1A1A"


def button_hover(button, on_hover, on_leave):
    button.bind("<Enter>", func=lambda e: button.config(background=on_hover))

    button.bind("<Leave>", func=lambda e: button.config(background=on_leave))


class MainMenu:

    def __init__(self):
        self.master = tk.Tk()
        self.master.title("RISC-V Pipeline Simulator")
        self.master.resizable(False, False)
        self.master.config(bg=back)
        
        # Ajustar tamaño de ventana según resolución de pantalla (80% de ancho, 85% de alto)
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()
        window_width = min(1200, int(screen_width * 0.8))
        window_height = min(750, int(screen_height * 0.85))
        
        self.lftPos = (screen_width - window_width) / 2
        self.topPos = (screen_height - window_height) / 2
        self.master.geometry("%dx%d+%d+%d" % (window_width, window_height, self.lftPos, self.topPos))

        self.var = tk.StringVar()
        self.list = []
        self.filtered_list = []
        self.first = True

        # Botones de la GUI

        self.editor_button = tk.Button(self.master, text="Editor", font=("Terminal", 20), width=10, height=2,
                                       pady=25, command=lambda: self.editor_window(), state=tk.DISABLED,
                                       bg="#3A3A3A", activebackground=back)
        self.compile_button = tk.Button(self.master, text="Compile", font=("Terminal", 20), width=10, height=2,
                                        pady=25, command=lambda: self.get_txt(), activebackground=back)
        self.memory_button = tk.Button(self.master, text="Memory", font=("Terminal", 20), width=10, height=2, pady=25,
                                       command=lambda: self.memory_window(), activebackground=back, state="disabled")

        self.editor_button.grid(column=0, row=0)
        self.compile_button.grid(column=0, row=2)
        self.memory_button.grid(column=0, row=1)

        button_hover(self.compile_button, "#3A3A3A", "SystemButtonFace")
        #button_hover(self.memory_button, "#3A3A3A", "SystemButtonFace")

        self.change_button = ttk.Combobox(self.master, font=("Terminal", 20), state="readonly", width=14, height=4)

        self.change_button["values"] = ('CPU_NH/CPU_HC', 'CPU_PS/CPU_SHC')
        self.change_button.current(0)
        #self.change_button.bind('<<ComboboxSelected>>', self.selected)

        self.change_button.grid(column=2, row=0)


        # Editor
        self.editor_tab = tk.Frame(self.master, bg=back, width=645, height=525)
        self.editor_tab.grid_propagate(False)
        self.editor_tab.grid(column=1, row=0, sticky="nsew", rowspan=30)

        self.code_entry = tk.Text(self.editor_tab, height=30, width=80)

        self.code_entry.grid(column=1, row=3, columnspan=5)
        self.editor_button.grid(column=0, row=0)

        # Processor
        self.processor_tab = tk.Frame(self.master, bg="#1A1A1A", width=1280, height=900)
        self.processor_tab.grid_propagate(False)

        # Path to log file
        self.log_path = os.path.join(os.path.dirname(__file__), "..", "log.txt")

        # Create processor view widget
        #self.processor_view = ProcessorView(self.processor_tab, self.log_path)
        #self.processor_view.pack(fill='both', expand=True)

        # Memory
        self.memory_tab = tk.Frame(self.master, bg=back, width=645, height=525)
        self.memory_tab.grid_propagate(False)
        self.cpu_label = tk.Label(self.memory_tab, text="CPU sin hazards / CPU Hazard Control", font=("Terminal", 20), height=2)
        self.memory_text1 = tk.Text(self.memory_tab, height=31, width=40)
        self.memory_text2 = tk.Text(self.memory_tab, height=31, width=40)

        self.cpu_label.grid(column=1, row=3, columnspan=6)
        self.memory_text1.grid(column=1, row=4, columnspan=3)
        self.memory_text2.grid(column=4, row=4, columnspan=3, padx=10)


    def get_txt(self):
        """Ejecuta las simulaciones y abre las ventanas de visualización"""
        self.list.clear()
        self.filtered_list.clear()
        txt = self.code_entry.get(1.0, "end").rstrip("\n")

        self.list = txt.split("\n")
        for i in range(len(self.list)):
            linea = self.list[i].split("#")[0].strip()
            self.filtered_list.append(linea)

        self.filtered_list = [item for item in self.filtered_list if item.strip()]

        # Validar que hay código para ejecutar
        if not self.filtered_list:
            messagebox.showwarning("Advertencia", "Por favor ingrese código RISC-V para simular")
            return

        self.master.focus_set()
        
        # Ejecutar simulaciones usando SimulatorRunner
        cpu_pair_index = self.change_button.current()
        
        # Mostrar mensaje de progreso
        progress_msg = messagebox.showinfo(
            "Ejecutando Simulaciones",
            "Ejecutando simulaciones del CPU...\nEsto puede tomar unos segundos.",
            parent=self.master
        )
        
        # Ejecutar las dos simulaciones
        success1, success2 = SimulatorRunner.run_dual_simulation(cpu_pair_index, self.list)
        
        if not (success1 and success2):
            messagebox.showerror(
                "Error en Simulación",
                "Ocurrió un error durante la simulación.\nRevise la consola para más detalles."
            )
            return
        
        # Habilitar botón de memoria
        self.memory_button.config(state="normal")
        
        # Configurar labels
        cpu_label = ["CPU sin Hazards / CPU con Hazard Control",
                     "CPU Prediccion de Saltos / CPU Prediccion de Saltos con Hazard"]
        cpu_title = ["CPU sin Hazards", "CPU Prediccion de Saltos",
                     "CPU con Hazard Control", "CPU Prediccion de Saltos con Hazard"]
        self.cpu_label.config(text=cpu_label[cpu_pair_index])
        
        # Obtener dimensiones de pantalla para posicionar ventanas
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()
        
        # Calcular tamaños de ventana (70% de pantalla)
        window_width = int(screen_width * 0.7)
        window_height = int(screen_height * 0.7)
        
        # Abrir ventanas de procesador con posiciones ajustadas
        # Ventana 1: lado izquierdo
        ProcessorWindow(
            self.master, back,
            cpu_title[cpu_pair_index],
            window_width, window_height,
            cpu_pair_index
        )
        
        # Ventana 2: lado derecho (con offset)
        ProcessorWindow(
            self.master, back,
            cpu_title[cpu_pair_index + 2],
            window_width, window_height,
            cpu_pair_index + 2
        )
        
        # Mostrar mensaje de éxito
        messagebox.showinfo(
            "Simulación Completada",
            "Las simulaciones se completaron exitosamente.\n"
            "Use los controles en las ventanas de procesador para navegar por los ciclos."
        )


    def editor_window(self):
        self.processor_tab.grid_forget()
        self.memory_tab.grid_forget()
        self.editor_button.unbind("<Enter>")
        self.editor_button.unbind("<Leave>")
        self.editor_button.config(state=tk.DISABLED)
        button_hover(self.compile_button, "#3A3A3A", "SystemButtonFace")
        button_hover(self.memory_button, "#3A3A3A", "SystemButtonFace")
        self.compile_button.config(state=tk.NORMAL, bg="SystemButtonFace")
        self.memory_button.config(state=tk.NORMAL, bg="SystemButtonFace")
        self.editor_tab.grid(column=1, row=0, sticky="nsew", rowspan=30)
        self.editor_tab.grid_propagate(False)

    def memory_window(self):
        self.editor_tab.grid_forget()
        self.processor_tab.grid_forget()
        self.memory_button.unbind("<Enter>")
        self.memory_button.unbind("<Leave>")
        self.memory_button.config(state=tk.DISABLED)
        button_hover(self.editor_button, "#3A3A3A", "SystemButtonFace")
        button_hover(self.compile_button, "#3A3A3A", "SystemButtonFace")
        self.editor_button.config(state=tk.NORMAL, bg="SystemButtonFace")
        self.compile_button.config(state=tk.NORMAL, bg="SystemButtonFace")
        self.master.focus_set()
        self.memory_tab.grid(column=1, row=0, sticky="nsew", rowspan=30)
        self.memory_tab.grid_propagate(False)

        # Get Memory File

        file_paths = ["memoria_salida.txt", "memoria_salida_prediccion.txt", "memoria_salida_hazard_control.txt",
                      "memoria_salida_prediccion_hazard_control.txt"]
        self.memory_text1.config(state=tk.NORMAL)
        self.memory_text2.config(state=tk.NORMAL)
        with open(file_paths[self.change_button.current()], "r") as file:
            content = file.read()
            self.memory_text1.delete(1.0, tk.END)
            self.memory_text1.insert(tk.END, content)
        with open(file_paths[self.change_button.current() + 2], "r") as file:
            content = file.read()
            self.memory_text2.delete(1.0, tk.END)
            self.memory_text2.insert(tk.END, content)
        self.memory_text1.config(state=tk.DISABLED)
        self.memory_text2.config(state=tk.DISABLED)



    def start(self):
        self.master.mainloop()


