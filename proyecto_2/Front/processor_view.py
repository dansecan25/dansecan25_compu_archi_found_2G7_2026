import tkinter as tk
from tkinter import ttk
import re
import os
from processor_diagram import ProcessorDiagram

# ─── Paleta ─────────────────────────────────────────────────────────────────
BG         = "#1A1A1A"
BG2        = "#222222"
BG3        = "#2A2A2A"
BORDER     = "#3A3A3A"
ACTIVE_CLR = "#2D5A8A"
IDLE_CLR   = "#2E2E2E"
ACTIVE_TXT = "#FFFFFF"
IDLE_TXT   = "#555555"
ACCENT     = "#5AADDD"
GREEN      = "#5ACD8A"
FG         = "#DDDDDD"
FG2        = "#999999"
MONO       = ("Courier", 9)
MONO_S     = ("Courier", 8)
SMALL      = ("Courier", 7)
LABEL_F    = ("Courier", 9, "bold")

ROW_EVEN   = "#1E1E1E"
ROW_ODD    = "#242424"
STALL_CLR  = "#8A3A3A"
STALL_TXT  = "#FF6B6B"

STAGE_NAMES_LOG  = ['Fetch', 'Decode', 'RegFile', 'Execute', 'Store']
STAGE_NAMES_DISP = ['IF',    'ID',     'EX',      'MEM',     'WB']


class LogParser:
    def __init__(self, log_path):
        self.log_path = log_path
        self.cycles = []
        self.instructions = []
        self.register_updates = {}
        self.current_cycle_idx = 0

    def parse(self):
        if not os.path.exists(self.log_path):
            print(f"Log file not found: {self.log_path}")
            return False

        with open(self.log_path, 'r', encoding='utf-8') as f:
            content = f.read()

        instr_match = re.search(r'(\d+) instrucciones cargadas.*?(?=\n\n)', content, re.DOTALL)
        if instr_match:
            instr_section = instr_match.group(0)
            instr_lines = re.findall(r'\[(\d+)\]\s+(.+)', instr_section)
            self.instructions = [(int(idx), instr.strip()) for idx, instr in instr_lines]

        cycle_pattern = r'\[CICLO\s+(\d+)\]\s+\[PC=\s*(\d+)\]\s+Estado del Pipeline:(.*?)(?=\n\n|\[CICLO|\Z)'
        for match in re.finditer(cycle_pattern, content, re.DOTALL):
            cycle_num = int(match.group(1))
            pc = int(match.group(2))
            pipeline_state = match.group(3)

            stages = {}
            for sm in re.finditer(r'(\w+):\s+(.+?)(?=\n|$)', pipeline_state):
                stages[sm.group(1).strip()] = sm.group(2).strip()

            cycle_end_pattern = rf'\[CICLO\s+{cycle_num}\].*?(?=\[CICLO|\Z)'
            cycle_section = re.search(cycle_end_pattern, content, re.DOTALL)

            completed_instr = None
            reg_updates = []

            if cycle_section:
                section_text = cycle_section.group(0)
                cm = re.search(r'\[COMPLETADA\]\s+(.+)', section_text)
                if cm:
                    completed_instr = cm.group(1).strip()

                for rm in re.finditer(r'\[STORE\]\s+Registro\s+(\w+)\s+<-\s+(\d+)', section_text):
                    rn, rv = rm.group(1), int(rm.group(2))
                    reg_updates.append((rn, rv))
                    self.register_updates[rn] = rv

                for ji in re.findall(r'\[STORE\]\s+JAL:\s+(.+)', section_text):
                    reg_updates.append(("JAL", ji))

            self.cycles.append({
                'cycle': cycle_num, 'pc': pc, 'stages': stages,
                'completed': completed_instr, 'reg_updates': reg_updates
            })

        return len(self.cycles) > 0

    def get_cycle_data(self, cycle_idx):
        if 0 <= cycle_idx < len(self.cycles):
            return self.cycles[cycle_idx]
        return None

    def get_total_cycles(self):
        return len(self.cycles)

    def _extract_instr_name(self, stage_value):
        if stage_value == 'Libre':
            return '–'
        m = re.match(r'Procesando:\s+(.+?)\s+\(\d+', stage_value)
        return m.group(1) if m else stage_value


class ProcessorView(tk.Frame):
    def __init__(self, parent, log_path, **kwargs):
        super().__init__(parent, bg=BG, **kwargs)
        self.log_path = log_path
        self.parser = LogParser(log_path)
        self.current_cycle = 0
        self.is_running = False
        self.animation_speed = 500
        self._speed = 1
        self.processor_diagram = None
        self.setup_ui()

    def setup_ui(self):
        # ── 1. CONTROL BAR ───────────────────────────────────────────────────
        ctrl = tk.Frame(self, bg=BG3, pady=4)
        ctrl.pack(fill='x', padx=6, pady=(6, 0))

        btn_style = dict(bg="#333333", fg=FG, font=("Courier", 9),
                         relief=tk.GROOVE, activebackground=BORDER,
                         bd=1, padx=8, pady=2)

        self.reset_btn     = tk.Button(ctrl, text='Reset',   command=self.reset,     **btn_style)
        self.step_back_btn = tk.Button(ctrl, text='◀ Back',  command=self.step_back, **btn_style)
        self.step_btn      = tk.Button(ctrl, text='Step ▶',  command=self.step,      **btn_style)
        self.run_btn       = tk.Button(ctrl, text='Run ▶▶',  command=self.run,       **btn_style)
        self.stop_btn      = tk.Button(ctrl, text='Stop ■',  command=self.stop,
                                       state='disabled', **btn_style)

        for b in (self.reset_btn, self.step_back_btn, self.step_btn,
                  self.run_btn, self.stop_btn):
            b.pack(side='left', padx=3)

        self.cycle_label = tk.Label(ctrl, text='Ciclo: 0 / 0',
                                    bg=BG3, fg=ACCENT, font=("Courier", 9, "bold"))
        self.cycle_label.pack(side='left', padx=12)

        self.pc_label = tk.Label(ctrl, text='PC: 0x0000',
                                 bg=BG3, fg=GREEN, font=("Courier", 9, "bold"))
        self.pc_label.pack(side='left', padx=8)

        tk.Label(ctrl, text='Velocidad:', bg=BG3, fg=FG2, font=SMALL).pack(
            side='left', padx=(12, 2))
        self._spd_var = tk.StringVar(value="1x")
        spd = ttk.Combobox(ctrl, textvariable=self._spd_var,
                           values=["1x", "2x", "4x", "8x"],
                           state="readonly", width=4)
        spd.pack(side='left')
        spd.bind("<<ComboboxSelected>>", self._on_speed_change)

        self._lbl_mode = tk.Label(ctrl, text="Step-by-step",
                                  bg=BG3, fg=FG2, font=SMALL)
        self._lbl_mode.pack(side='left', padx=12)

        # ── 2. MAIN SCROLLABLE AREA ──────────────────────────────────────────
        outer = tk.Frame(self, bg=BG)
        outer.pack(fill='both', expand=True, padx=6, pady=6)

        v_scroll = tk.Scrollbar(outer, orient='vertical')
        v_scroll.pack(side='right', fill='y')

        self._main_canvas = tk.Canvas(outer, bg=BG, highlightthickness=0,
                                      yscrollcommand=v_scroll.set)
        self._main_canvas.pack(side='left', fill='both', expand=True)
        v_scroll.config(command=self._main_canvas.yview)

        scroll_frame = tk.Frame(self._main_canvas, bg=BG)
        self._scroll_win = self._main_canvas.create_window(
            (0, 0), window=scroll_frame, anchor='nw')

        scroll_frame.bind("<Configure>", self._on_scroll_configure)
        self._main_canvas.bind("<Configure>", self._on_canvas_configure)

        def _mw(e):
            self._main_canvas.yview_scroll(int(-1*(e.delta/120)), "units")
        self._main_canvas.bind_all("<MouseWheel>", _mw)

        cf = scroll_frame

        # ── 3. ESTADO ACTUAL DEL PIPELINE ───────────────────────────────────
        self._build_pipeline_table(cf)

        # ── 4. DATAPATH / ARQUITECTURA ───────────────────────────────────────
        self._build_datapath_section(cf)

        # ── 5. HISTORIAL DEL PIPELINE ────────────────────────────────────────
        self._build_history_section(cf)

    def _build_pipeline_table(self, parent):
        wrapper = tk.LabelFrame(parent, text=" Estado actual del pipeline (5 etapas) ",
                                bg=BG, fg=FG2, font=SMALL, bd=1, relief=tk.GROOVE)
        wrapper.pack(fill='x', pady=(0, 6))

        hdr = tk.Frame(wrapper, bg=BG3)
        hdr.pack(fill='x', padx=4, pady=(4, 0))

        self._stage_cells = {}

        for i, (log_name, disp_name) in enumerate(
                zip(STAGE_NAMES_LOG, STAGE_NAMES_DISP)):
            col = tk.Frame(hdr, bg=BG3)
            col.grid(row=0, column=i, padx=2, pady=2, sticky='ew')
            hdr.grid_columnconfigure(i, weight=1)

            hdr_lbl = tk.Label(col, text=disp_name, bg=IDLE_CLR,
                               fg=IDLE_TXT, font=LABEL_F,
                               width=18, pady=3)
            hdr_lbl.pack(fill='x')

            val_lbl = tk.Label(col, text='–', bg=IDLE_CLR,
                               fg=IDLE_TXT, font=MONO,
                               width=18, pady=5, wraplength=160)
            val_lbl.pack(fill='x')

            self._stage_cells[log_name] = (hdr_lbl, val_lbl)

        info_bar = tk.Frame(wrapper, bg=BG)
        info_bar.pack(fill='x', padx=4, pady=(4, 4))

        self.instr_info_label = tk.Label(
            info_bar, text='Sin instruccion', bg=BG, fg=FG2,
            font=MONO_S, anchor='w', padx=6)
        self.instr_info_label.pack(fill='x')

    def _build_datapath_section(self, parent):
        wrapper = tk.LabelFrame(parent, text=" Datapath con registros de pipeline ",
                                bg=BG, fg=FG2, font=SMALL, bd=1, relief=tk.GROOVE)
        wrapper.pack(fill='x', pady=(0, 6))

        diagram_side = tk.Frame(wrapper, bg=BG)
        diagram_side.pack(side='left', fill='both', expand=True)

        h_sb = ttk.Scrollbar(diagram_side, orient='horizontal')
        v_sb = ttk.Scrollbar(diagram_side, orient='vertical')

        self.diagram_canvas = tk.Canvas(
            diagram_side, bg=BG, highlightthickness=0,
            xscrollcommand=h_sb.set, yscrollcommand=v_sb.set,
            width=860, height=280
        )
        h_sb.config(command=self.diagram_canvas.xview)
        v_sb.config(command=self.diagram_canvas.yview)

        self.diagram_canvas.grid(row=0, column=0, sticky='nsew')
        v_sb.grid(row=0, column=1, sticky='ns')
        h_sb.grid(row=1, column=0, sticky='ew')
        diagram_side.grid_rowconfigure(0, weight=1)
        diagram_side.grid_columnconfigure(0, weight=1)

        self.processor_diagram = ProcessorDiagram(self.diagram_canvas)
        self.diagram_canvas.configure(scrollregion=self.diagram_canvas.bbox('all'))

        # Register bank on the right
        reg_side = tk.Frame(wrapper, bg=BG2, width=200)
        reg_side.pack(side='right', fill='y', padx=(4, 4), pady=4)
        reg_side.pack_propagate(False)

        tk.Label(reg_side, text='Banco de Registros', bg=BG2, fg=FG,
                 font=LABEL_F).pack(pady=(6, 4))

        reg_c_frame = tk.Frame(reg_side, bg=BG2)
        reg_c_frame.pack(fill='both', expand=True)

        reg_canvas = tk.Canvas(reg_c_frame, bg=BG, highlightthickness=0)
        reg_sb = ttk.Scrollbar(reg_c_frame, orient='vertical',
                               command=reg_canvas.yview)
        self.reg_frame = tk.Frame(reg_canvas, bg=BG)

        reg_canvas.create_window((0, 0), window=self.reg_frame, anchor='nw')
        reg_canvas.configure(yscrollcommand=reg_sb.set)
        reg_canvas.pack(side='left', fill='both', expand=True)
        reg_sb.pack(side='right', fill='y')

        self.reg_labels = {}
        for i in range(32):
            rn = f'x{i}'
            lbl = tk.Label(self.reg_frame, text=f'{rn:3s}: 0',
                           bg=BG, fg=FG2, font=MONO_S, anchor='w', width=16)
            lbl.pack(pady=0, padx=4)
            self.reg_labels[rn] = lbl

        self.reg_frame.update_idletasks()
        reg_canvas.configure(scrollregion=reg_canvas.bbox('all'))

    def _build_history_section(self, parent):
        wrapper = tk.LabelFrame(parent,
                                text=" Historial del pipeline (todos los ciclos) ",
                                bg=BG, fg=FG2, font=SMALL, bd=1, relief=tk.GROOVE)
        wrapper.pack(fill='both', expand=True, pady=(0, 4))

        cols = ['Ciclo'] + STAGE_NAMES_DISP
        col_widths = [6, 22, 22, 22, 22, 22]

        hdr_row = tk.Frame(wrapper, bg=BG3)
        hdr_row.pack(fill='x', padx=4, pady=(4, 0))
        for col_txt, cw in zip(cols, col_widths):
            tk.Label(hdr_row, text=col_txt, bg=BG3, fg=ACCENT,
                     font=LABEL_F, width=cw, anchor='center',
                     pady=3).pack(side='left')

        list_frame_outer = tk.Frame(wrapper, bg=BG, height=200)
        list_frame_outer.pack(fill='both', expand=True, padx=4, pady=(0, 4))
        list_frame_outer.pack_propagate(False)

        hist_canvas = tk.Canvas(list_frame_outer, bg=BG, highlightthickness=0)
        hist_sb = ttk.Scrollbar(list_frame_outer, orient='vertical',
                                command=hist_canvas.yview)
        self._hist_inner = tk.Frame(hist_canvas, bg=BG)

        hist_canvas.create_window((0, 0), window=self._hist_inner, anchor='nw')
        hist_canvas.configure(yscrollcommand=hist_sb.set)
        hist_canvas.pack(side='left', fill='both', expand=True)
        hist_sb.pack(side='right', fill='y')

        self._hist_inner.bind("<Configure>",
            lambda e: hist_canvas.configure(scrollregion=hist_canvas.bbox('all')))

        self._hist_canvas = hist_canvas
        self._hist_col_widths = col_widths

    def _on_scroll_configure(self, event):
        self._main_canvas.configure(scrollregion=self._main_canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self._main_canvas.itemconfig(self._scroll_win, width=event.width)

    def _on_speed_change(self, event=None):
        self._speed = int(self._spd_var.get()[:-1])
        self.animation_speed = max(80, 1000 // self._speed)

    def _add_stage_components(self, stage_name, components, wires):
        stage_mapping = {
            'Fetch':   {'components': ['PC','PC_Adder','Inst_Mem','IF/ID'],
                        'wires': ['PC_to_IMem','PC_to_Adder','Adder_to_IFID','IMem_to_IFID']},
            'Decode':  {'components': ['Control','RegFile','SignExt','ID/EX'],
                        'wires': ['IFID_to_Control','IFID_to_RegFile','RegFile_to_IDEX','SignExt_to_IDEX']},
            'RegFile': {'components': ['ALU_Control','ALU','Mux_ALU_A','Mux_ALU_B','EX/MEM'],
                        'wires': ['IDEX_to_ALU','MuxA_to_ALU','MuxB_to_ALU','ALU_to_EXMEM']},
            'Execute': {'components': ['Data_Mem','Mux_PC','MEM/WB'],
                        'wires': ['EXMEM_to_DMem','DMem_to_MEMWB']},
            'Store':   {'components': ['Mux_WB'],
                        'wires': ['MEMWB_to_Mux','WB_to_RegFile']},
        }
        if stage_name in stage_mapping:
            m = stage_mapping[stage_name]
            components.extend(m['components'])
            wires.extend(m['wires'])

    def load_log(self):
        success = self.parser.parse()
        if success:
            self.current_cycle = 0
            self._rebuild_history()
            self.update_display()
            total = self.parser.get_total_cycles()
            self.cycle_label.config(text=f'Ciclo: 0 / {total}')
            return True
        else:
            self.instr_info_label.config(
                text='Error: No se pudo cargar el archivo de log')
            return False

    def _rebuild_history(self):
        for widget in self._hist_inner.winfo_children():
            widget.destroy()

        for row_idx, cycle_data in enumerate(self.parser.cycles):
            bg_row = ROW_EVEN if row_idx % 2 == 0 else ROW_ODD
            row = tk.Frame(self._hist_inner, bg=bg_row)
            row.pack(fill='x')

            tk.Label(row, text=str(cycle_data['cycle']),
                     bg=bg_row, fg=FG2, font=MONO_S,
                     width=self._hist_col_widths[0],
                     anchor='center').pack(side='left')

            stages = cycle_data['stages']
            for j, log_name in enumerate(STAGE_NAMES_LOG):
                val = stages.get(log_name, 'Libre')
                label_text = self.parser._extract_instr_name(val)
                is_stall = label_text.lower() == 'stall'
                cell_fg = STALL_TXT if is_stall else (FG if label_text != '–' else IDLE_TXT)
                cell_bg = STALL_CLR if is_stall else bg_row
                cw = self._hist_col_widths[j + 1]
                tk.Label(row, text=label_text,
                         bg=cell_bg, fg=cell_fg, font=MONO_S,
                         width=cw, anchor='center').pack(side='left')

        self._hist_canvas.yview_moveto(0)

    def _highlight_history_row(self, cycle_idx):
        rows = self._hist_inner.winfo_children()
        for i, row in enumerate(rows):
            is_current = (i == cycle_idx)
            bg = ACTIVE_CLR if is_current else (ROW_EVEN if i % 2 == 0 else ROW_ODD)
            row.config(bg=bg)
            for child in row.winfo_children():
                child.config(bg=bg)
        total = len(rows)
        if total > 0:
            self._hist_canvas.yview_moveto(max(0, cycle_idx / total - 0.1))

    def update_display(self):
        cycle_data = self.parser.get_cycle_data(self.current_cycle)
        if cycle_data is None:
            return

        total = self.parser.get_total_cycles()
        self.cycle_label.config(text=f"Ciclo: {cycle_data['cycle']} / {total}")
        self.pc_label.config(text=f"PC: 0x{cycle_data['pc']:04X}")

        stages = cycle_data['stages']
        active_components = []
        active_wires = []

        for log_name, (hdr_lbl, val_lbl) in self._stage_cells.items():
            stage_value = stages.get(log_name, 'Libre')
            instr = self.parser._extract_instr_name(stage_value)
            is_active = (instr != '–')

            hdr_lbl.config(
                bg=ACTIVE_CLR if is_active else IDLE_CLR,
                fg=ACTIVE_TXT if is_active else IDLE_TXT)
            val_lbl.config(
                text=instr,
                bg=ACTIVE_CLR if is_active else IDLE_CLR,
                fg=ACTIVE_TXT if is_active else IDLE_TXT)

            if is_active:
                self._add_stage_components(log_name, active_components, active_wires)

        if self.processor_diagram:
            self.processor_diagram.set_active_components(active_components)
            self.processor_diagram.set_active_wires(active_wires)

        info_text = f"Ciclo {cycle_data['cycle']}  |  PC = 0x{cycle_data['pc']:04X}"
        if cycle_data['completed']:
            info_text += f"  |  Completada: {cycle_data['completed']}"
        if cycle_data['reg_updates']:
            info_text += "  |  " + ", ".join(
                [f"{n}<-{v}" for n, v in cycle_data['reg_updates']])
        self.instr_info_label.config(text=info_text)

        for reg_name, reg_value in cycle_data['reg_updates']:
            if reg_name in self.reg_labels:
                self.reg_labels[reg_name].config(
                    text=f'{reg_name:3s}: {reg_value}',
                    fg=GREEN, font=("Courier", 8, "bold"))

        for reg_name, label in self.reg_labels.items():
            if not any(reg_name == r[0] for r in cycle_data['reg_updates']):
                label.config(fg=FG2, font=MONO_S)

        self._highlight_history_row(self.current_cycle)

    def reset(self):
        self.stop()
        self.current_cycle = 0
        for rn, lbl in self.reg_labels.items():
            lbl.config(text=f'{rn:3s}: 0', fg=FG2, font=MONO_S)
        if self.processor_diagram:
            self.processor_diagram.reset_all()
        self.update_display()
        self._lbl_mode.config(text="Step-by-step")

    def step(self):
        self.stop()
        if self.current_cycle < self.parser.get_total_cycles() - 1:
            self.current_cycle += 1
            self.update_display()

    def step_back(self):
        self.stop()
        if self.current_cycle > 0:
            self.current_cycle -= 1
            self._recalc_registers_up_to(self.current_cycle)
            self.update_display()

    def _recalc_registers_up_to(self, up_to_idx):
        for rn, lbl in self.reg_labels.items():
            lbl.config(text=f'{rn:3s}: 0', fg=FG2, font=MONO_S)
        for i in range(up_to_idx + 1):
            cd = self.parser.get_cycle_data(i)
            if cd:
                for rn, rv in cd['reg_updates']:
                    if rn in self.reg_labels:
                        self.reg_labels[rn].config(text=f'{rn:3s}: {rv}')

    def run(self):
        if not self.is_running:
            self.is_running = True
            self.run_btn.config(state='disabled')
            self.stop_btn.config(state='normal')
            self._lbl_mode.config(text="Automatico")
            self._run_cycle()

    def _run_cycle(self):
        if self.is_running and self.current_cycle < self.parser.get_total_cycles() - 1:
            self.current_cycle += 1
            self.update_display()
            self.after(self.animation_speed, self._run_cycle)
        else:
            self.stop()
            if self.current_cycle >= self.parser.get_total_cycles() - 1:
                self._lbl_mode.config(text="Completado")

    def stop(self):
        if self.is_running:
            self.is_running = False
            self.run_btn.config(state='normal')
            self.stop_btn.config(state='disabled')
            self._lbl_mode.config(text="Step-by-step")