"""
Vista del Procesador Uniciclo - CE 1107
Basado en el mockup: muestra diagrama de módulos, registros, memoria y controles.
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
FG         = "#DDDDDD"
FG2        = "#999999"
MONO       = ("Courier", 9)
MONO_S     = ("Courier", 8)
SMALL      = ("Courier", 7)
LABEL_F    = ("Courier", 9, "bold")


# ─── Parser del log uniciclo ──────────────────────────────────────────────────
class UnicicloLogParser:
    def __init__(self, log_path: str):
        self.log_path = log_path
        self.cycles   = []
        self._parse()

    def _parse(self):
        if not os.path.exists(self.log_path):
            return
        with open(self.log_path, encoding="utf-8") as f:
            content = f.read()

        blocks = re.split(r'\[CICLO\s+(\d+)\]', content)
        regs_state = {f"x{j}": 0 for j in range(32)}
        mem_state  = {}
        i = 1
        while i + 1 < len(blocks):
            num  = int(blocks[i])
            body = blocks[i+1]
            i += 2

            pc_m    = re.search(r'PC=(\S+)', body)
            instr_m = re.search(r'Instrucción:\s*(.+)', body)
            pc    = pc_m.group(1).strip() if pc_m else "-"
            instr = instr_m.group(1).strip() if instr_m else ""

            # Detectar escritura de registro: "= value → xN"
            for m in re.finditer(r'=\s*(-?\d+)\s*→\s*x(\d+)', body):
                regs_state[f"x{m.group(2)}"] = int(m.group(1))

            # Detectar escritura en memoria: "Mem[N] ← value"
            for m in re.finditer(r'Mem\[(\d+)\]\s*←\s*(-?\d+)', body):
                mem_state[int(m.group(1))] = int(m.group(2))

            active = self._active_modules(instr)

            self.cycles.append({
                "cycle"  : num,
                "pc"     : pc,
                "instr"  : instr,
                "body"   : body.strip(),
                "active" : active,
                "regs"   : dict(regs_state),
                "mem"    : dict(mem_state),
                "time_ns": num * 2.25,
            })

    def _active_modules(self, instr: str) -> set:
        lo = instr.lower()
        s  = {"PC", "IM", "Regs", "ALU", "Control", "+4", "MUX"}
        if any(x in lo for x in ("lw", "sw")):
            s.add("DM")
        if any(x in lo for x in ("addi", "lw", "sw", "beq", "blt", "bge", "jal", "jalr")):
            s.add("Sign Ext")
        return s


# ─── Canvas del diagrama datapath ────────────────────────────────────────────
class UnicleDiagram(tk.Canvas):
    M = {   # name: (x, y, w, h)
        "PC"      : (18,  105, 68, 55),
        "IM"      : (118, 105, 68, 55),
        "Regs"    : (228, 88,  82, 90),
        "Sign Ext": (228, 198, 82, 36),
        "ALU"     : (360, 88,  72, 90),
        "+4"      : (228, 38,  60, 30),
        "DM"      : (478, 88,  72, 90),
        "MUX"     : (602, 88,  28, 90),
        "Control" : (18,  218, 68, 44),
    }

    def __init__(self, parent, **kw):
        super().__init__(parent, bg=BG2, highlightthickness=0, **kw)
        self._ids: dict[str, list] = {}
        self._draw()

    def _cx(self, name):   # center x of module
        x,y,w,h = self.M[name]; return x+w//2
    def _cy(self, name):
        x,y,w,h = self.M[name]; return y+h//2
    def _right(self, name):
        x,y,w,h = self.M[name]; return x+w, y+h//2
    def _left(self, name):
        x,y,w,h = self.M[name]; return x, y+h//2
    def _top(self, name):
        x,y,w,h = self.M[name]; return x+w//2, y
    def _bot(self, name):
        x,y,w,h = self.M[name]; return x+w//2, y+h

    def _line(self, *pts, **kw):
        kw.setdefault("fill", BORDER)
        kw.setdefault("width", 1)
        kw.setdefault("arrow", tk.LAST)
        kw.setdefault("arrowshape", (5,7,3))
        flat = [c for p in pts for c in p]
        self.create_line(*flat, **kw)

    def _draw(self):
        M = self.M
        # ── Alambres (dibujados antes de los módulos)
        # PC → IM
        self._line(self._right("PC"), self._left("IM"))
        # IM → Regs
        self._line(self._right("IM"), self._left("Regs"))
        # Regs → ALU (Rs1)
        rx,ry,rw,rh = M["Regs"]
        ax,ay,aw,ah = M["ALU"]
        self._line((rx+rw, ry+22), (ax, ay+22))
        # Regs → ALU (Rs2)
        self._line((rx+rw, ry+65), (ax, ay+65))
        # Sign Ext → ALU (MUX)
        sx,sy,sw,sh = M["Sign Ext"]
        self._line((sx+sw, sy+18), (ax+aw//2+4, ay+90), (ax+aw//2+4, ay+65))
        # ALU → DM
        self._line(self._right("ALU"), self._left("DM"))
        # DM → MUX
        self._line(self._right("DM"), self._left("MUX"))
        # ALU → MUX (bypass, abajo)
        alr = ax+aw; aly = ay+45
        mux_x = M["MUX"][0]; mux_y = M["MUX"][1]+67
        self._line((alr, aly), (alr+18, aly), (alr+18, mux_y), (mux_x, mux_y))
        # MUX output
        mx2 = M["MUX"][0]+M["MUX"][2]
        my2 = M["MUX"][1]+45
        self.create_line(mx2, my2, mx2+30, my2, fill=BORDER, width=1)
        self.create_text(mx2+44, my2, text="WB", fill=FG2, font=SMALL)
        # PC → +4
        p4x,p4y,p4w,p4h = M["+4"]
        self._line((M["PC"][0]+M["PC"][2]//2, M["PC"][1]), (p4x+p4w//2, p4y+p4h))
        # +4 → PC feedback (loop)
        fbx = p4x+p4w//2; fby = p4y
        self._line((fbx, fby), (fbx, 10), (M["PC"][0]+M["PC"][2]//2, 10),
                   (M["PC"][0]+M["PC"][2]//2, M["PC"][1]))
        # IM → Sign Ext
        im_cx = M["IM"][0]+M["IM"][2]//2
        self._line((im_cx, M["IM"][1]+M["IM"][3]), (im_cx, sy+18), (sx, sy+18))
        # Control → ALU (dashed hint)
        cx2,cy2 = M["Control"][0]+M["Control"][2]//2, M["Control"][1]
        self.create_line(cx2, cy2, cx2, ay+ah+8, ax+aw//2, ay+ah+8,
                         ax+aw//2, ay+ah, fill="#444444", width=1, dash=(3,3))

        # ── Módulos
        for name, (x,y,w,h) in M.items():
            rect = self.create_rectangle(x, y, x+w, y+h,
                                         fill=IDLE_CLR, outline=BORDER, width=1)
            txt  = self.create_text(x+w//2, y+h//2, text=name,
                                    fill=IDLE_TXT, font=MONO)
            self._ids[name] = [rect, txt]

    def set_active(self, active: set):
        for name, ids in self._ids.items():
            if name in active:
                self.itemconfig(ids[0], fill=ACTIVE_CLR, outline=ACCENT, width=2)
                self.itemconfig(ids[1], fill=ACTIVE_TXT, font=("Courier", 9, "bold"))
            else:
                self.itemconfig(ids[0], fill=IDLE_CLR, outline=BORDER, width=1)
                self.itemconfig(ids[1], fill=IDLE_TXT, font=MONO)

    def reset_active(self):
        self.set_active(set())


# ─── Vista Uniciclo (Frame embebible) ─────────────────────────────────────────
class VistaUniciclo(tk.Frame):
    def __init__(self, parent, log_path: str, **kw):
        super().__init__(parent, bg=BG, **kw)
        self.log_path = log_path
        self.parser   = UnicicloLogParser(log_path)
        self.cycles   = self.parser.cycles
        self.cur_idx  = -1
        self._run_job = None
        self._speed   = 1
        self._build_ui()
        self._refresh()

    def reload(self, log_path: str):
        self.log_path = log_path
        self.parser   = UnicicloLogParser(log_path)
        self.cycles   = self.parser.cycles
        self.cur_idx  = -1
        self._refresh()

    # ── UI ────────────────────────────────────────────────────────────────
    def _build_ui(self):
        # Barra superior de estado
        top = tk.Frame(self, bg=BG3, pady=3)
        top.pack(fill=tk.X)

        self._v_cycle = self._stat(top, "Ciclo:",       "-",  8)
        self._v_pc    = self._stat(top, "PC:",          "-", 10)
        self._v_time  = self._stat(top, "Tiempo:",      "-", 10)
        self._v_instr = self._stat(top, "Instrucción:", "-", 30)

        # Cuerpo
        body = tk.Frame(self, bg=BG)
        body.pack(fill=tk.BOTH, expand=True, padx=5, pady=4)

        # Panel izquierdo: diagrama
        lf = tk.LabelFrame(body,
            text=" Diagrama del procesador uniciclo  (módulos activos resaltados) ",
            bg=BG2, fg=FG2, font=LABEL_F, bd=1, relief=tk.FLAT)
        lf.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0,4))

        self._diag = UnicleDiagram(lf, width=680, height=280)
        self._diag.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        note = tk.Label(lf,
            text="  • Cada instrucción se completa en un solo ciclo\n"
                 "  • Los módulos activos cambian según la instrucción",
            bg=BG2, fg=FG2, font=SMALL, justify=tk.LEFT)
        note.pack(anchor=tk.W, padx=6, pady=(0,4))

        # Panel derecho: registros + memoria
        right = tk.Frame(body, bg=BG)
        right.pack(side=tk.RIGHT, fill=tk.Y)
        self._build_regs(right)
        self._build_mem(right)

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

    def _build_regs(self, par):
        frm = tk.LabelFrame(par, text=" Registros ", bg=BG2, fg=FG2,
                            font=LABEL_F, bd=1, relief=tk.FLAT)
        frm.pack(fill=tk.X, pady=(0,3))
        self._reg_lbl: dict[str, tk.Label] = {}
        cols = tk.Frame(frm, bg=BG2)
        cols.pack(padx=3, pady=2)
        for i in range(32):
            col = i // 16
            row = i % 16
            tk.Label(cols, text=f"x{i:02d}=", bg=BG2, fg=FG2,
                     font=SMALL, anchor=tk.E).grid(row=row, column=col*2, sticky=tk.E)
            v = tk.Label(cols, text="0", bg=BG2, fg=FG, font=SMALL,
                         width=7, anchor=tk.W)
            v.grid(row=row, column=col*2+1, sticky=tk.W)
            self._reg_lbl[f"x{i}"] = v

    def _build_mem(self, par):
        frm = tk.LabelFrame(par, text=" Memoria ", bg=BG2, fg=FG2,
                            font=LABEL_F, bd=1, relief=tk.FLAT)
        frm.pack(fill=tk.BOTH, expand=True)
        self._mem_txt = tk.Text(frm, bg=BG2, fg=FG, font=SMALL,
                                width=22, height=10, state=tk.DISABLED,
                                relief=tk.FLAT, highlightthickness=0)
        sb = tk.Scrollbar(frm, command=self._mem_txt.yview)
        self._mem_txt.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self._mem_txt.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

    def _build_controls(self, par):
        kw = dict(bg="#333333", fg=FG, font=("Courier", 10), relief=tk.GROOVE,
                  activebackground=BORDER, bd=1, padx=10, pady=3)

        self._btn_step  = tk.Button(par, text="Step",  command=self._step,  **kw)
        self._btn_run   = tk.Button(par, text="Run",   command=self._run,   **kw)
        self._btn_reset = tk.Button(par, text="Reset", command=self._reset, **kw)

        for b in (self._btn_step, self._btn_run, self._btn_reset):
            b.pack(side=tk.LEFT, padx=4)

        tk.Label(par, text="Velocidad:", bg=BG3, fg=FG2, font=SMALL).pack(side=tk.LEFT, padx=(12,2))
        self._spd_var = tk.StringVar(value="1×")
        spd = ttk.Combobox(par, textvariable=self._spd_var,
                           values=["1×","2×","4×","8×"], state="readonly", width=4)
        spd.pack(side=tk.LEFT)
        spd.bind("<<ComboboxSelected>>",
                 lambda e: setattr(self, '_speed', int(self._spd_var.get()[:-1])))

        self._lbl_mode = tk.Label(par, text="Modo: Step-by-step",
                                  bg=BG3, fg=FG2, font=SMALL)
        self._lbl_mode.pack(side=tk.LEFT, padx=14)

        tk.Label(par,
            text="Hint: en uniciclo, 1 ciclo = 1 instrucción completa",
            bg=BG3, fg="#555555", font=SMALL).pack(side=tk.RIGHT, padx=8)

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
        self._lbl_mode.config(text="Modo: Step-by-step")
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
            self._v_time.config(text="-")
            self._v_instr.config(text="(sin ejecutar)")
            self._diag.reset_active()
            self._set_regs({f"x{i}": 0 for i in range(32)})
            self._set_mem({})
            return
        cy = self.cycles[self.cur_idx]
        pc = cy["pc"]
        try:    pc_str = f"0x{int(pc):04X}"
        except: pc_str = pc
        self._v_cycle.config(text=str(cy["cycle"]))
        self._v_pc.config(text=pc_str)
        self._v_time.config(text=f"{cy['time_ns']:.2f} ns")
        self._v_instr.config(text=cy["instr"] or "(fin del programa)")
        self._diag.set_active(cy["active"])
        self._set_regs(cy["regs"])
        self._set_mem(cy["mem"])

    def _set_regs(self, regs: dict):
        for k, lbl in self._reg_lbl.items():
            v = regs.get(k, 0)
            lbl.config(text=str(v), fg=GREEN if v != 0 else FG)

    def _set_mem(self, mem: dict):
        self._mem_txt.config(state=tk.NORMAL)
        self._mem_txt.delete("1.0", tk.END)
        if not mem:
            self._mem_txt.insert(tk.END, "(vacía)")
        else:
            for addr in sorted(mem):
                self._mem_txt.insert(tk.END, f"0x{addr*4:03X} = {mem[addr]}\n")
        self._mem_txt.config(state=tk.DISABLED)


# ─── Ventana independiente ────────────────────────────────────────────────────
class VentanaUniciclo(tk.Toplevel):
    def __init__(self, parent, log_path: str):
        super().__init__(parent)
        self.title("Vista del Procesador Uniciclo")
        self.configure(bg=BG)
        self.geometry("1020x580")
        self.resizable(True, True)
        VistaUniciclo(self, log_path).pack(fill=tk.BOTH, expand=True)
        self.protocol("WM_DELETE_WINDOW", self.destroy)


if __name__ == "__main__":
    import sys
    root = tk.Tk(); root.withdraw()
    lp = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(__file__), "log_uniciclo.txt")
    VentanaUniciclo(root, lp)
    root.mainloop()
