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
        # CPU 0,1 (Uniciclo/Multiciclo) van a la izquierda
        # CPU 2,3,4,5 (Pipeline) van a la derecha
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

        # Lista de archivos de log para cada CPU (índices 0-5)
        self.log_files = [
            "log_uniciclo.txt",                      # 0: CPU Uniciclo
            "log_multiciclo.txt",                    # 1: CPU Multiciclo
            "log.txt",                               # 2: CPU Pipeline sin Hazards
            "log_hazard_control.txt",                # 3: CPU Pipeline con Hazard Control
            "log_prediccion.txt",                    # 4: CPU Pipeline con Predicción
            "log_prediccion_hazard_control.txt"      # 5: CPU Pipeline Predicción + Hazard
        ]

        # Path to log file
        self.log_path = os.path.join(os.path.dirname(__file__), self.log_files[cpu])

        # Para CPUs no-pipeline (Uniciclo y Multiciclo), mostrar vista simple de texto
        if cpu in [0, 1]:  # Uniciclo o Multiciclo
            self.create_simple_log_view()
        else:  # CPUs Pipeline
            # Create processor view widget
            self.processor_view = ProcessorView(self.processor_tab, self.log_path)
            self.processor_view.pack(fill='both', expand=True)

            if self.processor_view:
               success = self.processor_view.load_log()
               if not success:
                    messagebox.showerror("Error", f"Failed to load simulation log: {self.log_files[cpu]}")

        self.process_win.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_simple_log_view(self):
        """Crea una vista simple de texto para CPUs no-pipeline (Uniciclo/Multiciclo)"""
        # Frame principal con scrollbar
        main_frame = tk.Frame(self.processor_tab, bg="#1A1A1A")
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Título
        title_label = tk.Label(
            main_frame,
            text="Log de Ejecución",
            font=("Courier", 14, "bold"),
            bg="#1A1A1A",
            fg="#FFFFFF"
        )
        title_label.pack(pady=(0, 10))
        
        # Text widget con scrollbar
        text_frame = tk.Frame(main_frame, bg="#1A1A1A")
        text_frame.pack(fill='both', expand=True)
        
        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        text_widget = tk.Text(
            text_frame,
            wrap=tk.WORD,
            font=("Courier", 10),
            bg="#2A2A2A",
            fg="#00FF00",
            yscrollcommand=scrollbar.set,
            padx=10,
            pady=10
        )
        text_widget.pack(side=tk.LEFT, fill='both', expand=True)
        scrollbar.config(command=text_widget.yview)
        
        # Cargar y mostrar el contenido del log
        try:
            if os.path.exists(self.log_path):
                with open(self.log_path, 'r', encoding='utf-8') as f:
                    log_content = f.read()
                text_widget.insert('1.0', log_content)
                text_widget.config(state=tk.DISABLED)  # Hacer solo lectura
            else:
                text_widget.insert('1.0', f"Error: No se encontró el archivo de log:\n{self.log_path}")
                text_widget.config(state=tk.DISABLED)
        except Exception as e:
            text_widget.insert('1.0', f"Error al cargar el log:\n{str(e)}")
            text_widget.config(state=tk.DISABLED)
        
        # Nota informativa
        note_label = tk.Label(
            main_frame,
            text="Nota: Los procesadores Uniciclo y Multiciclo no tienen visualización de pipeline.\n"
                 "Consulte el log completo arriba para ver la ejecución detallada.",
            font=("Arial", 9),
            bg="#1A1A1A",
            fg="#AAAAAA",
            justify=tk.LEFT
        )
        note_label.pack(pady=(10, 0))

    def on_closing(self):
        self.process_win.destroy()
        self.process_win.destroy()

