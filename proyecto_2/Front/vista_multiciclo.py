"""
Vista del Procesador Multiciclo - CE 1107
Basado en el mockup: muestra los módulos del datapath, FSM de estados activos,
registros temporales, y controles step/run/reset.
"""

import tkinter as tk
from tkinter import ttk
import os
import re

# ─── Paleta ───────────────────────────────────────────────────────────────────
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
ORANGE     = "#E0934A"
FG         = "#DDDDDD"
FG2        = "#999999"
MONO       = ("Courier", 9)
MONO_S     = ("Courier", 8)
SMALL      = ("Courier", 7)
LABEL_F    = ("Courier", 9, "bold")

# Etapas FSM del multiciclo
STAGES     = ["IF", "ID", "EX", "MEM", "WB"]
STAGE_FULL = {"IF":"FETCH","ID":"DECODE","EX":"EXECUTE","MEM":"MEMORY","WB":"WRITEBACK"}

# Módulos activos por etapa
STAGE_MODULES = {
    "FETCH"    : {"PC", "IM"},
    "DECODE"   : {"IR", "Regs"},
    "EXECUTE"  : {"ALU", "A", "B"},
    "MEMORY"   : {"DM", "ALUOut", "MDR"},
    "WRITEBACK": {"Regs", "MDR"},
    "IDLE"     : set(),
}


# ─── Parser del log multiciclo ────────────────────────────────────────────────
class MulticicloLogParser:
    def __init__(self, log_path: str):
        self.log_path = log_path
        self.cycles   = []   # un dict por ciclo de reloj
        self._parse()

    def _parse(self):
        if not os.path.exists(self.log_path):
            return
        with open(self.log_path, encoding="utf-8") as f:
            content = f.read()

        blocks = re.split(r'\[CICLO\s+(\d+)\]', content)
        regs_state = {f"x{j}": 0 for j in range(32)}
        mem_state  = {}
        # registros temporales
        temps = {"A": "-", "B": "-", "ALUOut": "-", "MDR": "-", "IR": "-"}
        pc    = "0"
        i     = 1

        while i + 1 < len(blocks):
            num  = int(blocks[i])
            body = blocks[i+1]
            i   += 2

            # Detectar etapa
            stage = "IDLE"
            for st in ["FETCH","DECODE","EXECUTE","MEMORY","WRITEBACK"]:
                if st in body.upper():
                    stage = st
                    break

            # PC desde FETCH
            pc_m = re.search(r'PC=(\S+)', body)
            if pc_m:
                pc = pc_m.group(1).strip()

            # IR
            ir_m = re.search(r"IR\s*←\s*Mem\[\d+\]\s*=\s*'(.+)'", body)
            if ir_m:
                temps["IR"] = ir_m.group(1).strip()

            # A y B en DECODE
            a_m = re.search(r'A\s*←\s*x\d+\s*=\s*(-?\d+)', body)
            b_m = re.search(r'B\s*←\s*(?:x\d+\s*=\s*|SignExt\([^)]+\)\s*=\s*)(-?\d+)', body)
            if a_m: temps["A"] = a_m.group(1)
            if b_m: temps["B"] = b_m.group(1)

            # ALUOut en EXECUTE
            alu_m = re.search(r'ALUOut\s*←[^=]+=\s*(-?\d+)', body)
            if alu_m: temps["ALUOut"] = alu_m.group(1)

            # MDR en MEMORY (lw)
            mdr_m = re.search(r'MDR\s*←\s*Mem\[\d+\]\s*=\s*(-?\d+)', body)
            if mdr_m: temps["MDR"] = mdr_m.group(1)

            # Registro destino en WRITEBACK
            for m in re.finditer(r'x(\d+)\s*←\s*(-?\d+)', body):
                regs_state[f"x{m.group(1)}"] = int(m.group(2))

            # Memoria
            for m in re.finditer(r'Mem\[(\d+)\]\s*←\s*(-?\d+)', body):
                mem_state[int(m.group(1))] = int(m.group(2))

            # Latencia por etapa (ns)
            lat = {"FETCH":1.0,"DECODE":0.5,"EXECUTE":1.5,"MEMORY":2.0,"WRITEBACK":0.5}
            time_ns = num * lat.get(stage, 1.0)

            self.cycles.append({
                "cycle"  : num,
                "pc"     : pc,
                "stage"  : stage,
                "body"   : body.strip(),
                "instr"  : temps["IR"],
                "temps"  : dict(temps),
                "regs"   : dict(regs_state),
                "mem"    : dict(mem_state),
                "active" : set(STAGE_MODULES.get(stage, set())),
                "time_ns": num * 1.1,
            })


# ─── Canvas del datapath multiciclo ──────────────────────────────────────────
class MultiDiagram(tk.Canvas):
    """
    Módulos: PC, IM, IR, Regs, ALU, A, B, ALUOut, MDR, DM
    Layout basado en el mockup del proyecto.
    """
    M = {
        "PC"    : (20,  30,  62, 44),
        "IM"    : (110, 30,  62, 44),
        "IR"    : (200, 30,  62, 44),
        "Regs"  : (290, 30,  68, 44),
        "ALU"   : (420, 30,  68, 44),
        "A"     : (20,  110, 62, 44),
        "B"     : (100, 110, 62, 44),
        "ALUOut": (200, 110, 62, 44),
        "MDR"   : (310, 110, 62, 44),
        "DM"    : (420, 110, 62, 44),
    }

    def __init__(self, parent, **kw):
        super().__init__(parent, bg=BG2, highlightthickness=0, **kw)
        self._ids: dict[str, list] = {}
        self._draw()

    def _draw(self):
        M = self.M
        def cx(n): x,y,w,h=M[n]; return x+w//2
        def cy(n): x,y,w,h=M[n]; return y+h//2
        def r(n):  x,y,w,h=M[n]; return x+w, y+h//2
        def l(n):  x,y,w,h=M[n]; return x,   y+h//2
        def b(n):  x,y,w,h=M[n]; return x+w//2, y+h
        def t(n):  x,y,w,h=M[n]; return x+w//2, y

        def wire(*pts):
            flat = [c for p in pts for c in p]
            self.create_line(*flat, fill=BORDER, width=1,
                             arrow=tk.LAST, arrowshape=(5,7,3))

        # Fila superior
        wire(r("PC"),  l("IM"))
        wire(r("IM"),  l("IR"))
        wire(r("IR"),  l("Regs"))
        wire(r("Regs"), l("ALU"))

        # PC → A (bajada)
        wire(b("PC"), t("A"))
        # Regs → A, B (bajada)
        wire((M["Regs"][0]+15, M["Regs"][1]+M["Regs"][3]),
             (M["A"][0]+30,    M["A"][1]))
        wire((M["Regs"][0]+45, M["Regs"][1]+M["Regs"][3]),
             (M["B"][0]+30,    M["B"][1]))
        # ALU → ALUOut
        wire(b("ALU"), t("ALUOut"))
        # DM → MDR
        wire(b("DM"),  t("MDR"))
        # ALUOut → DM
        wire(r("ALUOut"), l("DM"))
        # Nota de etapa
        x,y,w,h = M["DM"]
        self.create_text(cx("DM"), y+h+12, text="Data\nMem",
                         fill=FG2, font=SMALL, justify=tk.CENTER)

        # Módulos
        for name, (x,y,w,h) in M.items():
            rect = self.create_rectangle(x, y, x+w, y+h,
                                         fill=IDLE_CLR, outline=BORDER, width=1)
            txt  = self.create_text(x+w//2, y+h//2, text=name,
                                    fill=IDLE_TXT, font=MONO)
            self._ids[name] = [rect, txt]

        # Leyenda de etapa activa
        self._stage_lbl = self.create_text(260, 172,
            text="Estado activo: IDLE  |  (ningún módulo activo)",
            fill="#555555", font=SMALL)

    def set_active(self, active: set, stage: str):
        for name, ids in self._ids.items():
            if name in active:
                self.itemconfig(ids[0], fill=ACTIVE_CLR, outline=ACCENT, width=2)
                self.itemconfig(ids[1], fill=ACTIVE_TXT, font=("Courier",9,"bold"))
            else:
                self.itemconfig(ids[0], fill=IDLE_CLR, outline=BORDER, width=1)
                self.itemconfig(ids[1], fill=IDLE_TXT, font=MONO)
        parts = ", ".join(sorted(active)) if active else "ninguno"
        short = stage[:3] if stage != "IDLE" else "IDLE"
        self.itemconfig(self._stage_lbl,
            text=f"Estado activo: {short}  |  {', '.join(sorted(active)) if active else 'módulos en espera'}",
            fill=ACCENT if active else "#555555")

    def reset_active(self):
        self.set_active(set(), "IDLE")


# ─── Canvas de la FSM ─────────────────────────────────────────────────────────
class FSMCanvas(tk.Canvas):
    """Mini-diagrama de estados de la FSM multiciclo según el mockup."""

    POSITIONS = {
        "IF" : (50,  35),
        "ID" : (135, 35),
        "EX" : (220, 35),
        "MEM": (50,  100),
        "WB" : (135, 100),
    }
    R = 26   # radio del nodo

    def __init__(self, parent, **kw):
        super().__init__(parent, bg=BG2, highlightthickness=0, **kw)
        self._circles: dict[str, int] = {}
        self._labels:  dict[str, int] = {}
        self._draw_fsm()

    def _draw_fsm(self):
        P = self.POSITIONS; R = self.R
        edges = [
            ("IF","ID"), ("ID","EX"),
            ("EX","MEM"), ("EX","WB"),
            ("MEM","WB"),
            ("WB",None),   # → next instruction
        ]
        for (src, dst) in edges:
            if dst is None:
                sx, sy = P[src]
                self.create_line(sx+R, sy, sx+R+22, sy,
                                 fill=BORDER, width=1, arrow=tk.LAST, arrowshape=(5,7,3))
                self.create_text(sx+R+38, sy+12,
                                 text="→ siguiente\n  instrucción",
                                 fill=FG2, font=SMALL, justify=tk.LEFT)
                continue
            sx, sy = P[src]; dx, dy = P[dst]
            self.create_line(sx+R, sy, dx-R, dy,
                             fill=BORDER, width=1, arrow=tk.LAST, arrowshape=(5,7,3))

        for name, (cx, cy) in P.items():
            cid = self.create_oval(cx-R, cy-R, cx+R, cy+R,
                                   fill=IDLE_CLR, outline=BORDER, width=1)
            tid = self.create_text(cx, cy, text=name, fill=IDLE_TXT, font=MONO)
            self._circles[name] = cid
            self._labels[name]  = tid

    def set_active(self, stage_short: str):
        """Resaltar el nodo de la etapa activa."""
        for name in self.POSITIONS:
            if name == stage_short:
                self.itemconfig(self._circles[name],
                                fill=ACTIVE_CLR, outline=ACCENT, width=2)
                self.itemconfig(self._labels[name],
                                fill=ACTIVE_TXT, font=("Courier",9,"bold"))
            else:
                self.itemconfig(self._circles[name],
                                fill=IDLE_CLR, outline=BORDER, width=1)
                self.itemconfig(self._labels[name],
                                fill=IDLE_TXT, font=MONO)

    def reset_active(self):
        self.set_active("")


# ─── Vista Multiciclo (Frame embebible) ───────────────────────────────────────
class VistaMulticiclo(tk.Frame):
    def __init__(self, parent, log_path: str, **kw):
        super().__init__(parent, bg=BG, **kw)
        self.log_path = log_path
        self.parser   = MulticicloLogParser(log_path)
        self.cycles   = self.parser.cycles
        self.cur_idx  = -1
        self._run_job = None
        self._speed   = 1
        self._build_ui()
        self._refresh()

    def reload(self, log_path: str):
        self.log_path = log_path
        self.parser   = MulticicloLogParser(log_path)
        self.cycles   = self.parser.cycles
        self.cur_idx  = -1
        self._refresh()

    # ── UI ────────────────────────────────────────────────────────────────
    def _build_ui(self):
        # Barra superior
        top = tk.Frame(self, bg=BG3, pady=3)
        top.pack(fill=tk.X)
        self._v_cycle = self._stat(top, "Ciclo:",       "-",  8)
        self._v_pc    = self._stat(top, "PC:",          "-", 10)
        self._v_stage = self._stat(top, "Estado:",      "-", 12)
        self._v_instr = self._stat(top, "Instrucción:", "-", 28)

        # Cuerpo
        body = tk.Frame(self, bg=BG)
        body.pack(fill=tk.BOTH, expand=True, padx=5, pady=4)

        # ─ Panel izquierdo: diagrama datapath
        lf = tk.LabelFrame(body,
            text=" Procesador multiciclo (estado activo) ",
            bg=BG2, fg=FG2, font=LABEL_F, bd=1, relief=tk.FLAT)
        lf.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0,4))

        self._diag = MultiDiagram(lf, width=520, height=195)
        self._diag.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        # ─ Panel central: FSM
        fsm_frm = tk.LabelFrame(body,
            text=" Estado actual de la FSM ",
            bg=BG2, fg=FG2, font=LABEL_F, bd=1, relief=tk.FLAT)
        fsm_frm.pack(side=tk.LEFT, fill=tk.Y, padx=(0,4))

        self._fsm = FSMCanvas(fsm_frm, width=310, height=145)
        self._fsm.pack(padx=4, pady=4)

        # ─ Panel derecho: registros temporales + controles
        right = tk.Frame(body, bg=BG)
        right.pack(side=tk.RIGHT, fill=tk.Y)
        self._build_temps(right)
        self._build_regs(right)

        # Controles
        ctrl = tk.Frame(self, bg=BG3, pady=5)
        ctrl.pack(fill=tk.X, side=tk.BOTTOM)
        self._build_controls(ctrl)

    def _stat(self, par, label, init, width):
        f = tk.Frame(par, bg=BG3)
        f.pack(side=tk.LEFT, padx=8)
        tk.Label(f, text=label, bg=BG3, fg=FG2, font=SMALL).pack(side=tk.LEFT)
        v = tk.Label(f, text=init, bg=BG3, fg=ACCENT,
                     font=("Courier", 9, "bold"), width=width, anchor=tk.W)
        v.pack(side=tk.LEFT)
        return v

    def _build_temps(self, par):
        frm = tk.LabelFrame(par, text=" Registros temporales (snapshot) ",
                            bg=BG2, fg=FG2, font=LABEL_F, bd=1, relief=tk.FLAT)
        frm.pack(fill=tk.X, pady=(0,3))
        self._temp_lbls: dict[str, tk.Label] = {}
        for name in ("A", "B", "ALUOut", "MDR", "IR"):
            row = tk.Frame(frm, bg=BG2)
            row.pack(fill=tk.X, padx=6, pady=1)
            tk.Label(row, text=f"{name}:", bg=BG2, fg=FG2,
                     font=MONO_S, width=7, anchor=tk.E).pack(side=tk.LEFT)
            v = tk.Label(row, text="-", bg=BG2, fg=FG,
                         font=MONO_S, anchor=tk.W, width=22)
            v.pack(side=tk.LEFT)
            self._temp_lbls[name] = v

    def _build_regs(self, par):
        frm = tk.LabelFrame(par, text=" Registros ", bg=BG2, fg=FG2,
                            font=LABEL_F, bd=1, relief=tk.FLAT)
        frm.pack(fill=tk.BOTH, expand=True)
        self._reg_lbl: dict[str, tk.Label] = {}
        cols = tk.Frame(frm, bg=BG2)
        cols.pack(padx=3, pady=2)
        for i in range(32):
            col = i // 16
            row = i % 16
            tk.Label(cols, text=f"x{i:02d}=", bg=BG2, fg=FG2,
                     font=SMALL, anchor=tk.E).grid(row=row, column=col*2, sticky=tk.E)
            v = tk.Label(cols, text="0", bg=BG2, fg=FG,
                         font=SMALL, width=7, anchor=tk.W)
            v.grid(row=row, column=col*2+1, sticky=tk.W)
            self._reg_lbl[f"x{i}"] = v

    def _build_controls(self, par):
        kw = dict(bg="#333333", fg=FG, font=("Courier",10), relief=tk.GROOVE,
                  activebackground=BORDER, bd=1, padx=10, pady=3)
        self._btn_step  = tk.Button(par, text="Step",  command=self._step,  **kw)  # type: ignore
        self._btn_run   = tk.Button(par, text="Run",   command=self._run,   **kw)  # type: ignore
        self._btn_reset = tk.Button(par, text="Reset", command=self._reset, **kw)  # type: ignore
        for b in (self._btn_step, self._btn_run, self._btn_reset):
            b.pack(side=tk.LEFT, padx=4)

        tk.Label(par, text="Velocidad:", bg=BG3, fg=FG2, font=SMALL).pack(side=tk.LEFT, padx=(12,2))
        self._spd_var = tk.StringVar(value="1×")
        spd = ttk.Combobox(par, textvariable=self._spd_var,
                           values=["1×","2×","4×","8×"], state="readonly", width=4)
        spd.pack(side=tk.LEFT)
        spd.bind("<<ComboboxSelected>>",
                 lambda e: setattr(self, '_speed', int(self._spd_var.get()[:-1])))

        self._lbl_mode = tk.Label(par, text="Modo: Step-by-step (1 estado por click)",
                                  bg=BG3, fg=FG2, font=SMALL)
        self._lbl_mode.pack(side=tk.LEFT, padx=14)

        tk.Label(par,
            text="Hint: en multiciclo, 1 ciclo = 1 estado\n"
                 "una instrucción puede requerir 3-5 ciclos.",
            bg=BG3, fg="#555555", font=SMALL, justify=tk.LEFT).pack(side=tk.RIGHT, padx=8)

    # ── Control ──────────────────────────────────────────────────────────
    def _step(self):
        self._stop_run()
        if self.cur_idx + 1 < len(self.cycles):
            self.cur_idx += 1
            self._refresh()

    def _run(self):
        if self._run_job:
            self._stop_run(); return
        self._lbl_mode.config(text="Modo: Automático")
        self._btn_run.config(text="Pause")
        self._auto()

    def _auto(self):
        if self.cur_idx + 1 < len(self.cycles):
            self.cur_idx += 1
            self._refresh()
            delay = max(80, 1000 // self._speed)
            self._run_job = self.after(delay, self._auto)
        else:
            self._stop_run()
            self._lbl_mode.config(text="Modo: Completado ✓")

    def _stop_run(self):
        if self._run_job:
            self.after_cancel(self._run_job)
            self._run_job = None
        self._lbl_mode.config(text="Modo: Step-by-step (1 estado por click)")
        self._btn_run.config(text="Run")

    def _reset(self):
        self._stop_run()
        self.cur_idx = -1
        self._refresh()

    # ── Actualización ─────────────────────────────────────────────────────
    def _refresh(self):
        if self.cur_idx < 0 or not self.cycles:
            self._v_cycle.config(text="-")
            self._v_pc.config(text="-")
            self._v_stage.config(text="-")
            self._v_instr.config(text="(sin ejecutar)")
            self._diag.reset_active()
            self._fsm.reset_active()
            for lbl in self._temp_lbls.values():
                lbl.config(text="-", fg=FG)
            for lbl in self._reg_lbl.values():
                lbl.config(text="0", fg=FG)
            return

        cy = self.cycles[self.cur_idx]
        pc = cy["pc"]
        try:    pc_str = f"0x{int(pc):04X}"
        except: pc_str = pc

        stage     = cy["stage"]
        stage_sh  = {v: k for k, v in STAGE_FULL.items()}.get(stage, stage[:2] if stage else "")

        self._v_cycle.config(text=str(cy["cycle"]))
        self._v_pc.config(text=pc_str)
        self._v_stage.config(text=stage_sh if stage_sh else "IDLE")
        self._v_instr.config(text=cy["instr"] or "(fin del programa)")

        self._diag.set_active(cy["active"], stage)
        # Solo actualizar FSM si stage_sh es válido
        if stage_sh and stage_sh in FSMCanvas.POSITIONS:
            self._fsm.set_active(stage_sh)
        else:
            self._fsm.reset_active()

        # Registros temporales
        temps = cy["temps"]
        for name, lbl in self._temp_lbls.items():
            val = temps.get(name, "-")
            lbl.config(text=str(val),
                       fg=ORANGE if name in cy["active"] else FG)

        # Banco de registros
        regs = cy["regs"]
        for k, lbl in self._reg_lbl.items():
            v = regs.get(k, 0)
            lbl.config(text=str(v), fg=GREEN if v != 0 else FG)


# ─── Ventana independiente ────────────────────────────────────────────────────
class VentanaMulticiclo(tk.Toplevel):
    def __init__(self, parent, log_path: str):
        super().__init__(parent)
        self.title("Vista del Procesador Multiciclo")
        self.configure(bg=BG)
        self.geometry("1100x600")
        self.resizable(True, True)
        VistaMulticiclo(self, log_path).pack(fill=tk.BOTH, expand=True)
        self.protocol("WM_DELETE_WINDOW", self.destroy)


if __name__ == "__main__":
    import sys
    root = tk.Tk(); root.withdraw()
    lp = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(__file__), "log_multiciclo.txt")
    VentanaMulticiclo(root, lp)
    root.mainloop()
