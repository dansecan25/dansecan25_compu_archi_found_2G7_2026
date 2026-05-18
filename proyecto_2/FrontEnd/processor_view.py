import tkinter as tk
from tkinter import ttk
import re
import os


class LogParser:
    """Parsea el archivo log.txt para extraer datos de ejecución del pipeline."""

    def __init__(self, log_path):
        self.log_path = log_path
        self.cycles = []
        self.instructions = []
        self.register_updates = {}
        self.current_cycle_idx = 0

    def parse(self):
        """Parsea el archivo de log y extrae la información de todos los ciclos."""
        if not os.path.exists(self.log_path):
            print(f"Log file not found: {self.log_path}")
            return False

        with open(self.log_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extraer la lista de instrucciones
        instr_match = re.search(r'(\d+) instrucciones cargadas.*?(?=\n\n)', content, re.DOTALL)
        if instr_match:
            instr_section = instr_match.group(0)
            instr_lines = re.findall(r'\[(\d+)\]\s+(.+)', instr_section)
            self.instructions = [(int(idx), instr.strip()) for idx, instr in instr_lines]

        # Extraer información de cada ciclo
        cycle_pattern = r'\[CICLO\s+(\d+)\]\s+\[PC=\s*(\d+)\]\s+Estado del Pipeline:(.*?)(?=\n\n|\[CICLO|\Z)'
        cycle_matches = re.finditer(cycle_pattern, content, re.DOTALL)

        for match in cycle_matches:
            cycle_num = int(match.group(1))
            pc = int(match.group(2))
            pipeline_state = match.group(3)

            # Extraer estados de cada etapa
            stages = {}
            stage_pattern = r'(\w+):\s+(.+?)(?=\n|$)'
            for stage_match in re.finditer(stage_pattern, pipeline_state):
                stage_name = stage_match.group(1).strip()
                stage_value = stage_match.group(2).strip()
                stages[stage_name] = stage_value

            # Buscar instrucción completada y updates de registros para este ciclo
            cycle_end_pattern = rf'\[CICLO\s+{cycle_num}\].*?(?=\[CICLO|\Z)'
            cycle_section = re.search(cycle_end_pattern, content, re.DOTALL)

            completed_instr = None
            reg_updates = []

            if cycle_section:
                section_text = cycle_section.group(0)

                completed_match = re.search(r'\[COMPLETADA\]\s+(.+)', section_text)
                if completed_match:
                    completed_instr = completed_match.group(1).strip()

                reg_pattern = r'\[STORE\]\s+Registro\s+(\w+)\s+<-\s+(\d+)'
                for reg_match in re.finditer(reg_pattern, section_text):
                    reg_name = reg_match.group(1)
                    reg_value = int(reg_match.group(2))
                    reg_updates.append((reg_name, reg_value))
                    self.register_updates[reg_name] = reg_value

                jal_pattern = r'\[STORE\]\s+JAL:\s+(.+)'
                jal_matches = re.findall(jal_pattern, section_text)
                if jal_matches:
                    for jal_info in jal_matches:
                        reg_updates.append(("JAL", jal_info))

            cycle_data = {
                'cycle': cycle_num,
                'pc': pc,
                'stages': stages,
                'completed': completed_instr,
                'reg_updates': reg_updates
            }

            self.cycles.append(cycle_data)

        return len(self.cycles) > 0

    def get_cycle_data(self, cycle_idx):
        if 0 <= cycle_idx < len(self.cycles):
            return self.cycles[cycle_idx]
        return None

    def get_total_cycles(self):
        return len(self.cycles)


class PipelineStage(tk.Canvas):
    """Representación visual de una etapa del pipeline."""

    def __init__(self, parent, stage_name, width=180, height=100, **kwargs):
        super().__init__(parent, width=width, height=height, bg='#2B2B2B',
                         highlightthickness=1, highlightbackground='#4A4A4A', **kwargs)

        self.stage_name = stage_name
        self.width = width
        self.height = height

        self.box = self.create_rectangle(10, 10, width - 10, height - 10,
                                         fill='#3A3A3A', outline='#5A5A5A', width=2)

        self.name_text = self.create_text(width // 2, 25, text=stage_name,
                                          fill='#FFFFFF', font=('Arial', 10, 'bold'))

        self.instr_text = self.create_text(width // 2, 55, text='Libre',
                                           fill='#888888', font=('Arial', 9), width=width - 30)

    def update_stage(self, instruction_text, is_busy=False):
        """Actualiza la etapa con la instrucción actual."""
        if instruction_text == "Libre":
            self.itemconfig(self.box, fill='#3A3A3A', outline='#5A5A5A')
            self.itemconfig(self.instr_text, text='Libre', fill='#888888')
        else:
            match = re.match(r'Procesando:\s+(.+?)\s+\((\d+)\s+ciclos?\s+restantes?\)', instruction_text)
            if match:
                instr = match.group(1)
                cycles_left = match.group(2)
                display_text = f"{instr}\n({cycles_left} cycles)"
            else:
                display_text = instruction_text

            self.itemconfig(self.box, fill='#4A6A4A', outline='#6ADA6A')
            self.itemconfig(self.instr_text, text=display_text, fill='#FFFFFF')


class ProcessorView(tk.Frame):
    """Componente principal de visualización del procesador."""

    def __init__(self, parent, log_path, **kwargs):
        super().__init__(parent, bg='#1A1A1A', **kwargs)

        self.log_path = log_path
        self.parser = LogParser(log_path)
        self.current_cycle = 0
        self.is_running = False
        self.animation_speed = 500  # milisegundos

        self.setup_ui()

    def setup_ui(self):
        """Construye la interfaz."""
        # Panel de controles arriba
        control_frame = tk.Frame(self, bg='#2A2A2A', height=60)
        control_frame.pack(fill='x', padx=5, pady=5)
        control_frame.pack_propagate(False)

        btn_style = {'font': ('Arial', 10), 'bg': '#4A4A4A', 'fg': 'white',
                     'activebackground': '#5A5A5A', 'relief': 'raised', 'bd': 2}

        self.reset_btn = tk.Button(control_frame, text='⟲ Reset', command=self.reset, **btn_style)
        self.reset_btn.pack(side='left', padx=3, pady=10)

        self.step_back_btn = tk.Button(control_frame, text='◀ Step Back',
                                       command=self.step_back, **btn_style)
        self.step_back_btn.pack(side='left', padx=3, pady=10)

        self.step_btn = tk.Button(control_frame, text='▶ Step', command=self.step, **btn_style)
        self.step_btn.pack(side='left', padx=3, pady=10)

        self.run_btn = tk.Button(control_frame, text='▶▶ Run', command=self.run, **btn_style)
        self.run_btn.pack(side='left', padx=3, pady=10)

        self.stop_btn = tk.Button(control_frame, text='⏸ Stop', command=self.stop,
                                  state='disabled', **btn_style)
        self.stop_btn.pack(side='left', padx=3, pady=10)

        # Info de ciclo y PC
        self.cycle_label = tk.Label(control_frame, text='Cycle: 0 / 0',
                                    bg='#2A2A2A', fg='white', font=('Arial', 11, 'bold'))
        self.cycle_label.pack(side='left', padx=20)

        self.pc_label = tk.Label(control_frame, text='PC: 0',
                                 bg='#2A2A2A', fg='#6ADA6A', font=('Arial', 11, 'bold'))
        self.pc_label.pack(side='left', padx=10)

        # Control de velocidad
        tk.Label(control_frame, text='Speed:', bg='#2A2A2A', fg='white',
                 font=('Arial', 9)).pack(side='left', padx=(20, 5))

        self.speed_scale = tk.Scale(control_frame, from_=100, to=2000, orient='horizontal',
                                    bg='#2A2A2A', fg='white', highlightthickness=0,
                                    length=120, command=self.update_speed)
        self.speed_scale.set(500)
        self.speed_scale.pack(side='left', padx=5)

        # Contenedor central: pipeline + register file
        main_frame = tk.Frame(self, bg='#1A1A1A')
        main_frame.pack(fill='both', expand=True, padx=5, pady=5)

        # Pipeline (izquierda)
        pipeline_frame = tk.Frame(main_frame, bg='#1A1A1A')
        pipeline_frame.pack(side='left', fill='both', expand=True)

        tk.Label(pipeline_frame, text='Pipeline Stages', bg='#1A1A1A',
                 fg='white', font=('Arial', 12, 'bold')).pack(pady=(0, 10))

        stages_frame = tk.Frame(pipeline_frame, bg='#1A1A1A')
        stages_frame.pack(pady=20)

        self.stages = {}
        stage_names = ['Fetch', 'Decode', 'RegFile', 'Execute', 'Store']
        for i, name in enumerate(stage_names):
            stage = PipelineStage(stages_frame, name, width=160, height=90)
            stage.grid(row=0, column=i * 2, padx=5)
            self.stages[name] = stage

            # Flecha entre etapas
            if i < len(stage_names) - 1:
                arrow_canvas = tk.Canvas(stages_frame, width=20, height=90,
                                         bg='#1A1A1A', highlightthickness=0)
                arrow_canvas.create_line(0, 45, 18, 45, fill='#6ADA6A',
                                         width=2, arrow='last')
                arrow_canvas.grid(row=0, column=i * 2 + 1)

        # Register file (derecha)
        reg_frame = tk.Frame(main_frame, bg='#2A2A2A', width=220)
        reg_frame.pack(side='right', fill='y', padx=(10, 0))
        reg_frame.pack_propagate(False)

        tk.Label(reg_frame, text='Register File', bg='#2A2A2A',
                 fg='white', font=('Arial', 11, 'bold')).pack(pady=5)

        reg_scroll_frame = tk.Frame(reg_frame, bg='#1A1A1A')
        reg_scroll_frame.pack(fill='both', expand=True, padx=5, pady=5)

        canvas = tk.Canvas(reg_scroll_frame, bg='#1A1A1A', highlightthickness=0)
        scrollbar = ttk.Scrollbar(reg_scroll_frame, orient='vertical', command=canvas.yview)
        self.reg_inner_frame = tk.Frame(canvas, bg='#1A1A1A')

        self.reg_inner_frame.bind(
            '<Configure>',
            lambda e: canvas.configure(scrollregion=canvas.bbox('all'))
        )

        canvas.create_window((0, 0), window=self.reg_inner_frame, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # Crear etiquetas para los 32 registros
        self.reg_labels = {}
        for i in range(32):
            reg_name = f'x{i}'
            label = tk.Label(self.reg_inner_frame, text=f'{reg_name}: 0',
                             bg='#1A1A1A', fg='#AAAAAA', font=('Courier', 9),
                             anchor='w', width=20)
            label.pack(fill='x', padx=5, pady=1)
            self.reg_labels[reg_name] = label

        # Abajo: info de instrucción
        instr_info_frame = tk.Frame(self, bg='#2A2A2A', height=80)
        instr_info_frame.pack(fill='x', padx=5, pady=(0, 5))
        instr_info_frame.pack_propagate(False)

        tk.Label(instr_info_frame, text='Current Instruction Info', bg='#2A2A2A',
                 fg='white', font=('Arial', 10, 'bold')).pack(pady=(5, 2))

        self.instr_info_label = tk.Label(instr_info_frame, text='No instruction',
                                         bg='#1A1A1A', fg='#AAAAAA',
                                         font=('Courier', 9), anchor='w',
                                         padx=10, pady=5)
        self.instr_info_label.pack(fill='both', expand=True, padx=10, pady=(0, 5))

    def update_speed(self, value):
        self.animation_speed = int(value)

    def load_log(self):
        """Carga y parsea el archivo de log."""
        success = self.parser.parse()
        if success:
            self.current_cycle = 0
            self.update_display()
            total = self.parser.get_total_cycles()
            self.cycle_label.config(text=f'Cycle: 0 / {total}')
            return True
        else:
            self.instr_info_label.config(text='Error: Could not load log file')
            return False

    def update_display(self):
        """Actualiza todos los elementos visuales según el ciclo actual."""
        cycle_data = self.parser.get_cycle_data(self.current_cycle)

        if cycle_data is None:
            return

        total = self.parser.get_total_cycles()
        self.cycle_label.config(text=f"Cycle: {cycle_data['cycle']} / {total}")
        self.pc_label.config(text=f"PC: {cycle_data['pc']}")

        # Actualizar las etapas del pipeline
        stages = cycle_data['stages']
        for stage_name, stage_widget in self.stages.items():
            stage_value = stages.get(stage_name, 'Libre')
            stage_widget.update_stage(stage_value)

        # Actualizar info de instrucción
        info_text = f"Cycle {cycle_data['cycle']}: PC={cycle_data['pc']}"
        if cycle_data['completed']:
            info_text += f"\n✓ Completed: {cycle_data['completed']}"
        if cycle_data['reg_updates']:
            info_text += "\n" + ", ".join([f"{name}={val}" for name, val in cycle_data['reg_updates']])

        self.instr_info_label.config(text=info_text)

        # Actualizar register file
        for reg_update in cycle_data['reg_updates']:
            reg_name, reg_value = reg_update
            if reg_name in self.reg_labels:
                self.reg_labels[reg_name].config(
                    text=f'{reg_name}: {reg_value}',
                    fg='#6ADA6A',
                    font=('Courier', 9, 'bold')
                )

        # Restaurar color de los registros no actualizados
        for reg_name, label in self.reg_labels.items():
            if not any(reg_name == r[0] for r in cycle_data['reg_updates']):
                label.config(fg='#AAAAAA', font=('Courier', 9))

    def reset(self):
        """Vuelve al ciclo 0."""
        self.stop()
        self.current_cycle = 0

        for reg_name, label in self.reg_labels.items():
            label.config(text=f'{reg_name}: 0', fg='#AAAAAA', font=('Courier', 9))

        self.update_display()

    def step(self):
        """Avanza un ciclo."""
        if self.current_cycle < self.parser.get_total_cycles() - 1:
            self.current_cycle += 1
            self.update_display()

    def step_back(self):
        """Retrocede un ciclo."""
        if self.current_cycle > 0:
            self.current_cycle -= 1
            # Recalcular el estado de los registros hasta este punto
            self.reset()
            for i in range(self.current_cycle + 1):
                cycle_data = self.parser.get_cycle_data(i)
                if cycle_data:
                    for reg_update in cycle_data['reg_updates']:
                        reg_name, reg_value = reg_update
                        if reg_name in self.reg_labels:
                            self.reg_labels[reg_name].config(text=f'{reg_name}: {reg_value}')
            self.update_display()

    def run(self):
        """Corre todos los ciclos automáticamente."""
        if not self.is_running:
            self.is_running = True
            self.run_btn.config(state='disabled')
            self.stop_btn.config(state='normal')
            self._run_cycle()

    def _run_cycle(self):
        if self.is_running and self.current_cycle < self.parser.get_total_cycles() - 1:
            self.current_cycle += 1
            self.update_display()
            self.after(self.animation_speed, self._run_cycle)
        else:
            self.stop()

    def stop(self):
        self.is_running = False
        self.run_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
