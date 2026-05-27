import tkinter as tk
from tkinter import ttk
import re
import os
from processor_diagram import ProcessorDiagram

# ─── Paleta (igual que vista_uniciclo y vista_multiciclo) ────────────────────
BG         = "#1A1A1A"
BG2        = "#222222"
BG3        = "#2A2A2A"
BORDER     = "#3A3A3A"
ACTIVE_CLR = "#2D5A8A"
IDLE_CLR   = "#2E2E2E"
ACTIVE_TXT = "#FFFFFF"
IDLE_TXT   = "#777777"
ACCENT     = "#5AADDD"
GREEN      = "#5ACD8A"
FG         = "#DDDDDD"
FG2        = "#999999"
MONO       = ("Courier", 9)
MONO_S     = ("Courier", 8)
SMALL      = ("Courier", 7)
LABEL_F    = ("Courier", 9, "bold")


class LogParser:
    """Parse the log.txt file to extract pipeline execution data"""

    def __init__(self, log_path):
        self.log_path = log_path
        self.cycles = []
        self.instructions = []
        self.register_updates = {}
        self.current_cycle_idx = 0

    def parse(self):
        """Parse the log file and extract all cycle information"""
        if not os.path.exists(self.log_path):
            print(f"Log file not found: {self.log_path}")
            return False

        with open(self.log_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract instructions list
        instr_match = re.search(r'(\d+) instrucciones cargadas.*?(?=\n\n)', content, re.DOTALL)
        if instr_match:
            instr_section = instr_match.group(0)
            instr_lines = re.findall(r'\[(\d+)\]\s+(.+)', instr_section)
            self.instructions = [(int(idx), instr.strip()) for idx, instr in instr_lines]

        # Extract cycle information
        cycle_pattern = r'\[CICLO\s+(\d+)\]\s+\[PC=\s*(\d+)\]\s+Estado del Pipeline:(.*?)(?=\n\n|\[CICLO|\Z)'
        cycle_matches = re.finditer(cycle_pattern, content, re.DOTALL)

        for match in cycle_matches:
            cycle_num = int(match.group(1))
            pc = int(match.group(2))
            pipeline_state = match.group(3)

            # Extract stage states
            stages = {}
            stage_pattern = r'(\w+):\s+(.+?)(?=\n|$)'
            for stage_match in re.finditer(stage_pattern, pipeline_state):
                stage_name = stage_match.group(1).strip()
                stage_value = stage_match.group(2).strip()
                stages[stage_name] = stage_value

            # Look for completed instruction and register updates after this cycle
            cycle_end_pattern = rf'\[CICLO\s+{cycle_num}\].*?(?=\[CICLO|\Z)'
            cycle_section = re.search(cycle_end_pattern, content, re.DOTALL)

            completed_instr = None
            reg_updates = []

            if cycle_section:
                section_text = cycle_section.group(0)

                # Check for completed instruction
                completed_match = re.search(r'\[COMPLETADA\]\s+(.+)', section_text)
                if completed_match:
                    completed_instr = completed_match.group(1).strip()

                # Check for register updates
                reg_pattern = r'\[STORE\]\s+Registro\s+(\w+)\s+<-\s+(\d+)'
                for reg_match in re.finditer(reg_pattern, section_text):
                    reg_name = reg_match.group(1)
                    reg_value = int(reg_match.group(2))
                    reg_updates.append((reg_name, reg_value))
                    self.register_updates[reg_name] = reg_value

                # Check for JAL updates
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
        """Get data for a specific cycle index"""
        if 0 <= cycle_idx < len(self.cycles):
            return self.cycles[cycle_idx]
        return None

    def get_total_cycles(self):
        """Get total number of cycles"""
        return len(self.cycles)


class PipelineStage(tk.Canvas):
    """Visual representation of a single pipeline stage"""

    def __init__(self, parent, stage_name, width=180, height=100, **kwargs):
        super().__init__(parent, width=width, height=height, bg=BG2,
                        highlightthickness=1, highlightbackground=BORDER, **kwargs)

        self.stage_name = stage_name
        self.width = width
        self.height = height

        # Draw stage box
        self.box = self.create_rectangle(10, 10, width-10, height-10,
                                         fill=IDLE_CLR, outline=BORDER, width=2)

        # Stage name label
        self.name_text = self.create_text(width//2, 25, text=stage_name,
                                         fill=ACTIVE_TXT, font=LABEL_F)

        # Instruction text
        self.instr_text = self.create_text(width//2, 55, text='Libre',
                                          fill=IDLE_TXT, font=MONO, width=width-30)

    def update_stage(self, instruction_text, is_busy=False):
        """Update the stage with current instruction"""
        if instruction_text == "Libre":
            self.itemconfig(self.box, fill=IDLE_CLR, outline=BORDER)
            self.itemconfig(self.instr_text, text='Libre', fill=IDLE_TXT)
        else:
            # Parse "Procesando: instruction (X ciclos restantes)"
            match = re.match(r'Procesando:\s+(.+?)\s+\((\d+)\s+ciclos?\s+restantes?\)', instruction_text)
            if match:
                instr = match.group(1)
                cycles_left = match.group(2)
                display_text = f"{instr}\n({cycles_left} cycles)"
            else:
                display_text = instruction_text

            self.itemconfig(self.box, fill=ACTIVE_CLR, outline=ACCENT)
            self.itemconfig(self.instr_text, text=display_text, fill=ACTIVE_TXT)


class ProcessorView(tk.Frame):
    """Main processor visualization component"""

    def __init__(self, parent, log_path, **kwargs):
        super().__init__(parent, bg=BG, **kwargs)

        self.log_path = log_path
        self.parser = LogParser(log_path)
        self.current_cycle = 0
        self.is_running = False
        self.animation_speed = 500  # milliseconds
        self._speed = 1  # Velocidad multiplicador (1×, 2×, 4×, 8×)
        self.processor_diagram = None  # Will be created in setup_ui

        self.setup_ui()

    def setup_ui(self):
        """Setup the user interface"""
        # Control panel at top (fixed, no scroll)
        control_frame = tk.Frame(self, bg=BG3, pady=5)
        control_frame.pack(fill='x', padx=5, pady=5, side='top')

        # Control buttons (mismo estilo que multiciclo/uniciclo)
        btn_style = {'bg': "#333333", 'fg': FG, 'font': ("Courier", 10),
                    'relief': tk.GROOVE, 'activebackground': BORDER,
                    'bd': 1, 'padx': 10, 'pady': 3}

        self.reset_btn = tk.Button(control_frame, text='Reset', command=self.reset, **btn_style)  # type: ignore
        self.reset_btn.pack(side='left', padx=4)

        self.step_back_btn = tk.Button(control_frame, text='◀ Back',
                                       command=self.step_back, **btn_style)  # type: ignore
        self.step_back_btn.pack(side='left', padx=4)

        self.step_btn = tk.Button(control_frame, text='Step', command=self.step, **btn_style)  # type: ignore
        self.step_btn.pack(side='left', padx=4)

        self.run_btn = tk.Button(control_frame, text='Run', command=self.run, **btn_style)  # type: ignore
        self.run_btn.pack(side='left', padx=4)

        self.stop_btn = tk.Button(control_frame, text='Stop', command=self.stop,
                                 state='disabled', **btn_style)  # type: ignore
        self.stop_btn.pack(side='left', padx=4)

        # Cycle info
        self.cycle_label = tk.Label(control_frame, text='Ciclo: 0 / 0',
                                   bg=BG3, fg=ACCENT, font=("Courier", 9, "bold"))
        self.cycle_label.pack(side='left', padx=14)

        self.pc_label = tk.Label(control_frame, text='PC: 0',
                                bg=BG3, fg=GREEN, font=("Courier", 9, "bold"))
        self.pc_label.pack(side='left', padx=10)

        # Speed control (Combobox como en multiciclo)
        tk.Label(control_frame, text='Velocidad:', bg=BG3, fg=FG2,
                font=SMALL).pack(side='left', padx=(12, 2))
        
        self._spd_var = tk.StringVar(value="1×")
        spd = ttk.Combobox(control_frame, textvariable=self._spd_var,
                          values=["1×", "2×", "4×", "8×"], state="readonly", width=4)
        spd.pack(side='left')
        spd.bind("<<ComboboxSelected>>", self._on_speed_change)

        # Mode label
        self._lbl_mode = tk.Label(control_frame, text="Modo: Step-by-step",
                                 bg=BG3, fg=FG2, font=SMALL)
        self._lbl_mode.pack(side='left', padx=14)

        # Main content area con scrollbar
        # Canvas y scrollbar para hacer scroll vertical
        main_canvas = tk.Canvas(self, bg=BG, highlightthickness=0)
        scrollbar = tk.Scrollbar(self, orient='vertical', command=main_canvas.yview)
        
        # Frame scrollable que contendrá todo el contenido
        scrollable_frame = tk.Frame(main_canvas, bg=BG)
        scrollable_frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        )
        
        main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas y scrollbar
        main_canvas.pack(side='left', fill='both', expand=True, padx=(5, 0), pady=5)
        scrollbar.pack(side='right', fill='y', pady=5)
        
        # Bind mouse wheel para scroll
        def _on_mousewheel(event):
            main_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        main_canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Ahora content_frame es el scrollable_frame
        content_frame = scrollable_frame

        # Sección superior: Pipeline y Registros lado a lado
        top_section = tk.Frame(content_frame, bg=BG)
        top_section.pack(fill='x', padx=5, pady=5)

        # Left side: Pipeline visualization
        pipeline_frame = tk.Frame(top_section, bg=BG)
        pipeline_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))

        # Title
        tk.Label(pipeline_frame, text='Etapas del Pipeline', bg=BG, fg=FG,
                font=LABEL_F).pack(pady=(0, 10))

        # Pipeline stages container
        stages_container = tk.Frame(pipeline_frame, bg=BG)
        stages_container.pack(fill='both', expand=True)

        # Create pipeline stages
        self.stages = {}
        stage_names = ['Fetch', 'Decode', 'RegFile', 'Execute', 'Store']

        for i, stage_name in enumerate(stage_names):
            stage_widget = PipelineStage(stages_container, stage_name, width=160, height=90)
            stage_widget.grid(row=0, column=i, padx=5, pady=5)
            self.stages[stage_name] = stage_widget

        # Pipeline arrows
        arrow_canvas = tk.Canvas(stages_container, height=30, bg=BG,
                                highlightthickness=0)
        arrow_canvas.grid(row=1, column=0, columnspan=len(stage_names), sticky='ew')

        # Draw arrows between stages
        for i in range(len(stage_names) - 1):
            x_start = (i + 1) * 170 - 10
            x_end = x_start + 20
            arrow_canvas.create_line(x_start, 15, x_end, 15, arrow=tk.LAST,
                                    fill=GREEN, width=2)

        # Right side: Register file and info
        info_frame = tk.Frame(top_section, bg=BG2, width=280)
        info_frame.pack(side='right', fill='y', padx=(5, 0))
        info_frame.pack_propagate(False)

        # Register file
        tk.Label(info_frame, text='Banco de Registros', bg=BG2, fg=FG,
                font=LABEL_F).pack(pady=(10, 5))

        # Scrollable register display
        reg_container = tk.Frame(info_frame, bg=BG2)
        reg_container.pack(fill='both', expand=True, padx=10, pady=5)

        reg_canvas = tk.Canvas(reg_container, bg=BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(reg_container, orient='vertical', command=reg_canvas.yview)

        self.reg_frame = tk.Frame(reg_canvas, bg=BG)

        reg_canvas.create_window((0, 0), window=self.reg_frame, anchor='nw')
        reg_canvas.configure(yscrollcommand=scrollbar.set)

        reg_canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # Initialize register labels
        self.reg_labels = {}
        for i in range(32):
            reg_name = f'x{i}'
            reg_label = tk.Label(self.reg_frame, text=f'{reg_name}: 0',
                               bg=BG, fg=FG2, font=MONO,
                               anchor='w', width=18)
            reg_label.pack(pady=1, padx=5)
            self.reg_labels[reg_name] = reg_label

        self.reg_frame.update_idletasks()
        reg_canvas.configure(scrollregion=reg_canvas.bbox('all'))

        # ====== PROCESSOR DIAGRAM SECTION ======
        diagram_frame = tk.Frame(self, bg=BG)
        diagram_frame.pack(fill='both', expand=True, padx=5, pady=5)

        # Title for diagram section
        tk.Label(diagram_frame, text='Arquitectura del Procesador', bg=BG, fg=FG,
                font=LABEL_F).pack(pady=(0, 5))

        # Create scrollable canvas for processor diagram
        diagram_container = tk.Frame(diagram_frame, bg=BG2)
        diagram_container.pack(fill='both', expand=True)

        # Canvas with scrollbars
        h_scrollbar = ttk.Scrollbar(diagram_container, orient='horizontal')
        v_scrollbar = ttk.Scrollbar(diagram_container, orient='vertical')

        self.diagram_canvas = tk.Canvas(
            diagram_container,
            bg=BG,
            highlightthickness=0,
            xscrollcommand=h_scrollbar.set,
            yscrollcommand=v_scrollbar.set,
            width=1200,
            height=350
        )

        h_scrollbar.config(command=self.diagram_canvas.xview)
        v_scrollbar.config(command=self.diagram_canvas.yview)

        # Grid layout for canvas and scrollbars
        self.diagram_canvas.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')

        diagram_container.grid_rowconfigure(0, weight=1)
        diagram_container.grid_columnconfigure(0, weight=1)

        # Create the processor diagram
        self.processor_diagram = ProcessorDiagram(self.diagram_canvas)

        # Configure scroll region
        self.diagram_canvas.configure(scrollregion=self.diagram_canvas.bbox('all'))

        # Bottom: Instruction info
        instr_info_frame = tk.Frame(self, bg=BG3, height=80)
        instr_info_frame.pack(fill='x', padx=5, pady=(0, 5))
        instr_info_frame.pack_propagate(False)

        tk.Label(instr_info_frame, text='Información de Instrucción Actual', bg=BG3,
                fg=FG, font=LABEL_F).pack(pady=(5, 2))

        self.instr_info_label = tk.Label(instr_info_frame, text='Sin instrucción',
                                         bg=BG, fg=FG2,
                                         font=MONO, anchor='w',
                                         padx=10, pady=5)
        self.instr_info_label.pack(fill='both', expand=True, padx=10, pady=(0, 5))

    def _on_speed_change(self, event=None):
        """Callback cuando cambia la velocidad en el Combobox"""
        speed_str = self._spd_var.get()
        self._speed = int(speed_str[:-1])  # Quitar el '×' y convertir a int
        # Actualizar animation_speed basado en el multiplicador
        self.animation_speed = max(80, 1000 // self._speed)

    def update_speed(self, value):
        """Update animation speed (legacy method for compatibility)"""
        self.animation_speed = int(value)

    def _add_stage_components(self, stage_name: str, components: list, wires: list):
        """
        Map pipeline stage to processor components and wires
        Args:
            stage_name: Name of pipeline stage from log ('Fetch', 'Decode', 'RegFile', 'Execute', 'Store')
            components: List to append active component names
            wires: List to append active wire names

        Mapping from log names to pipeline stages:
            Fetch (log) -> Fetch (IF)
            Decode (log) -> Decode (ID)
            RegFile (log) -> Execute (EX)
            Execute (log) -> Data Memory (MEM)
            Store (log) -> WriteBack (WB)
        """
        stage_mapping = {
            # Fetch stage (IF)
            'Fetch': {
                'components': ['PC', 'PC_Adder', 'Inst_Mem', 'IF/ID'],
                'wires': ['PC_to_IMem', 'PC_to_Adder', 'Adder_to_IFID', 'IMem_to_IFID']
            },
            # Decode stage (ID)
            'Decode': {
                'components': ['Control', 'RegFile', 'SignExt', 'ID/EX'],
                'wires': ['IFID_to_Control', 'IFID_to_RegFile', 'RegFile_to_IDEX', 'SignExt_to_IDEX']
            },
            # RegFile in log = Execute stage (EX)
            'RegFile': {
                'components': ['ALU_Control', 'ALU', 'Mux_ALU_A', 'Mux_ALU_B', 'EX/MEM'],
                'wires': ['IDEX_to_ALU', 'MuxA_to_ALU', 'MuxB_to_ALU', 'ALU_to_EXMEM']
            },
            # Execute in log = Data Memory stage (MEM)
            'Execute': {
                'components': ['Data_Mem', 'Mux_PC', 'MEM/WB'],
                'wires': ['EXMEM_to_DMem', 'DMem_to_MEMWB']
            },
            # Store in log = WriteBack stage (WB)
            'Store': {
                'components': ['Mux_WB'],
                'wires': ['MEMWB_to_Mux', 'WB_to_RegFile']
            }
        }

        if stage_name in stage_mapping:
            mapping = stage_mapping[stage_name]
            components.extend(mapping['components'])
            wires.extend(mapping['wires'])

    def load_log(self):
        """Load and parse the log file"""
        success = self.parser.parse()
        if success:
            self.current_cycle = 0
            self.update_display()
            total = self.parser.get_total_cycles()
            self.cycle_label.config(text=f'Ciclo: 0 / {total}')
            return True
        else:
            self.instr_info_label.config(text='Error: No se pudo cargar el archivo de log')
            return False

    def update_display(self):
        """Update all visual elements based on current cycle"""
        cycle_data = self.parser.get_cycle_data(self.current_cycle)

        if cycle_data is None:
            return

        # Update cycle and PC labels
        total = self.parser.get_total_cycles()
        self.cycle_label.config(text=f"Ciclo: {cycle_data['cycle']} / {total}")
        self.pc_label.config(text=f"PC: {cycle_data['pc']}")

        # Update pipeline stages
        stages = cycle_data['stages']
        active_components = []
        active_wires = []

        for stage_name, stage_widget in self.stages.items():
            stage_value = stages.get(stage_name, 'Libre')
            stage_widget.update_stage(stage_value)

            # If stage is active, determine which components to highlight
            if stage_value != "Libre":
                self._add_stage_components(stage_name, active_components, active_wires)

        # Update processor diagram
        if self.processor_diagram:
            self.processor_diagram.set_active_components(active_components)
            self.processor_diagram.set_active_wires(active_wires)

        # Update instruction info
        info_text = f"Cycle {cycle_data['cycle']}: PC={cycle_data['pc']}"
        if cycle_data['completed']:
            info_text += f"\n✓ Completed: {cycle_data['completed']}"
        if cycle_data['reg_updates']:
            info_text += "\n" + ", ".join([f"{name}={val}" for name, val in cycle_data['reg_updates']])

        self.instr_info_label.config(text=info_text)

        # Update register file
        for reg_update in cycle_data['reg_updates']:
            reg_name, reg_value = reg_update
            if reg_name in self.reg_labels:
                self.reg_labels[reg_name].config(
                    text=f'{reg_name}: {reg_value}',
                    fg=GREEN,
                    font=("Courier", 9, "bold")
                )

        # Reset non-updated registers to normal color
        for reg_name, label in self.reg_labels.items():
            if not any(reg_name == r[0] for r in cycle_data['reg_updates']):
                current_text = label.cget('text')
                label.config(fg=FG2, font=MONO)

    def reset(self):
        """Reset to cycle 0"""
        self.stop()
        self.current_cycle = 0

        # Reset all register displays
        for reg_name, label in self.reg_labels.items():
            label.config(text=f'{reg_name}: 0', fg=FG2, font=MONO)

        # Reset processor diagram
        if self.processor_diagram:
            self.processor_diagram.reset_all()

        self.update_display()
        self._lbl_mode.config(text="Modo: Step-by-step")

    def step(self):
        """Step forward one cycle"""
        self.stop()  # Detener si está corriendo
        if self.current_cycle < self.parser.get_total_cycles() - 1:
            self.current_cycle += 1
            self.update_display()

    def step_back(self):
        """Step back one cycle"""
        self.stop()  # Detener si está corriendo
        if self.current_cycle > 0:
            self.current_cycle -= 1
            # Need to recalculate register state up to this point
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
        """Run through all cycles automatically"""
        if not self.is_running:
            self.is_running = True
            self.run_btn.config(state='disabled')
            self.stop_btn.config(state='normal')
            self._lbl_mode.config(text="Modo: Automático")
            self._run_cycle()

    def _run_cycle(self):
        """Internal method to run one cycle in animation"""
        if self.is_running and self.current_cycle < self.parser.get_total_cycles() - 1:
            self.current_cycle += 1
            self.update_display()
            self.after(self.animation_speed, self._run_cycle)
        else:
            self.stop()
            if self.current_cycle >= self.parser.get_total_cycles() - 1:
                self._lbl_mode.config(text="Modo: Completado ✓")

    def stop(self):
        """Stop the animation"""
        if self.is_running:
            self.is_running = False
            self.run_btn.config(state='normal')
            self.stop_btn.config(state='disabled')
            self._lbl_mode.config(text="Modo: Step-by-step")
