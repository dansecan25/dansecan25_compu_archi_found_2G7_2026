from typing import List, Dict
from collections import deque


class ProcessorSimulator:
    def __init__(self, code: List[str]):
        self.code_raw = code
        self.code: List[str] = self._clean_code(code)

        # Últimas 4 instrucciones ejecutadas (FIFO)
        self.ultimos4instrucciones = deque(maxlen=4)

        # Estado del procesador
        self.registers = [0] * 32        # x0–x31
        self.PC = 0                      # Program Counter
        self.memory: Dict[int, int] = {} # Memoria
        self.labels = {}                 # Label → línea

        self._find_labels()


    # ----------------------------------------------------
    # Limpia comentarios y líneas vacías
    # ----------------------------------------------------
    def _clean_code(self, code):
        cleaned = []
        for line in code:
            line = line.strip()
            if line == "" or line.startswith("#") or line.startswith("."):
                continue
            cleaned.append(line)
        return cleaned


    # ----------------------------------------------------
    # Encuentra labels y guarda su índice
    # ----------------------------------------------------
    def _find_labels(self):
        new_code = []
        for i, line in enumerate(self.code):
            if line.endswith(":"):
                label = line.replace(":", "")
                self.labels[label] = len(new_code)
            else:
                new_code.append(line)
        self.code = new_code


    # ----------------------------------------------------
    # Ejecuta el programa completo
    # ----------------------------------------------------
    def run(self):
        while self.PC < len(self.code):
            line = self.code[self.PC]
            print(f"[PC={self.PC}] Ejecutando → {line}")
            self.execute(line)

        print("\nÚltimas 4 instrucciones ejecutadas:")
        print(list(self.ultimos4instrucciones))


    # ----------------------------------------------------
    # Registrar última instrucción ejecutada
    # ----------------------------------------------------
    def instrucciones_executed(self, nombre: str):
        self.ultimos4instrucciones.append(nombre)


    # ----------------------------------------------------
    # Decodificador / Dispatcher
    # ----------------------------------------------------
    def execute(self, line: str):
        parts = line.replace(",", "").split()

        instr = parts[0]
        args = parts[1:]

        if instr == "addi": self._addi(args)
        elif instr == "add": self._add(args)
        elif instr == "sub": self._sub(args)
        elif instr == "lw": self._lw(args)
        elif instr == "sw": self._sw(args)
        elif instr == "la": self._la(args)
        elif instr == "blt": self._blt(args)
        elif instr == "beq": self._beq(args)
        elif instr == "jal": self._jal(args)
        elif instr == "nop": self._nop()
        else:
            print("ERROR: instrucción desconocida", instr)
            self.PC += 1
            return

        # x0 siempre debe ser 0
        self.registers[0] = 0


    # ----------------------------------------------------
    # Helpers
    # ----------------------------------------------------
    def reg(self, x):
        return int(x.replace("x", ""))

    def _parse_offset(self, operand):
        # Ejemplo: 0(x5)
        off, reg = operand.split("(")
        reg = reg.replace(")", "")
        return int(off), self.reg(reg)


    # ====================================================
    # IMPLEMENTACIÓN DE INSTRUCCIONES
    # ====================================================

    def _addi(self, args):
        rd = self.reg(args[0])
        rs1 = self.reg(args[1])
        imm = int(args[2])
        self.registers[rd] = self.registers[rs1] + imm
        self.PC += 1
        self.instrucciones_executed(f"addi x{rd} x{rs1} {imm}")

    def _add(self, args):
        rd = self.reg(args[0])
        rs1 = self.reg(args[1])
        rs2 = self.reg(args[2])
        self.registers[rd] = self.registers[rs1] + self.registers[rs2]
        self.PC += 1
        self.instrucciones_executed(f"add x{rd} x{rs1} x{rs2}")

    def _sub(self, args):
        rd = self.reg(args[0])
        rs1 = self.reg(args[1])
        rs2 = self.reg(args[2])
        self.registers[rd] = self.registers[rs1] - self.registers[rs2]
        self.PC += 1
        self.instrucciones_executed(f"sub x{rd} x{rs1} x{rs2}")

    def _lw(self, args):
        rd = self.reg(args[0])
        offset, rs1 = self._parse_offset(args[1])
        addr = self.registers[rs1] + offset
        self.registers[rd] = self.memory.get(addr, 0)
        self.PC += 1
        self.instrucciones_executed(f"lw x{rd} {offset}(x{rs1})")

    def _sw(self, args):
        rs2 = self.reg(args[0])
        offset, rs1 = self._parse_offset(args[1])
        addr = self.registers[rs1] + offset
        self.memory[addr] = self.registers[rs2]
        self.PC += 1
        self.instrucciones_executed(f"sw x{rs2} {offset}(x{rs1})")

    def _la(self, args):
        rd = self.reg(args[0])
        label = args[1]
        addr = self.labels.get(label, 0)
        self.registers[rd] = addr
        self.PC += 1
        self.instrucciones_executed(f"la x{rd} {label}")

    def _blt(self, args):
        rs1 = self.reg(args[0])
        rs2 = self.reg(args[1])
        label = args[2]
        if self.registers[rs1] < self.registers[rs2]:
            self.PC = self.labels[label]
        else:
            self.PC += 1
        self.instrucciones_executed(f"blt x{rs1} x{rs2} {label}")

    def _beq(self, args):
        rs1 = self.reg(args[0])
        rs2 = self.reg(args[1])
        label = args[2]
        if self.registers[rs1] == self.registers[rs2]:
            self.PC = self.labels[label]
        else:
            self.PC += 1
        self.instrucciones_executed(f"beq x{rs1} x{rs2} {label}")

    def _jal(self, args):
        rd = self.reg(args[0])
        label = args[1]
        self.registers[rd] = self.PC + 1
        self.PC = self.labels[label]
        self.instrucciones_executed(f"jal x{rd} {label}")

    def _nop(self):
        self.PC += 1
        self.instrucciones_executed("nop")
        self.registers[0] = 0



# =============================
# PROGRAMA DE PRUEBA (tu código)
# =============================

riscv_code = [
    "#=========================================================",
    "# PROGRAMA: Conteo de saltos (branch y jump)",
    "# OBJETIVO: Realizar miles de saltos condicionales e",
    "#           incondicionales y documentar cuántos ocurren.",
    "# COMPATIBLE CON: Ripes (RISC-V RV32I)",
    "#=========================================================",
    "",
    "        .data",
    "count:  .word 0             # Contador de iteraciones",
    "limit:  .word 5000          # Límite (miles de saltos)",
    "msg:    .string \"Fin del programa\\n\"",
    "",
    "        .text",
    "        .globl _start",
    "",
    "_start:",
    "        #-------------------------------------------------",
    "        # Inicialización",
    "        #-------------------------------------------------",
    "        la x5, count         # x5 = dirección del contador",
    "        la x6, limit         # x6 = dirección del límite",
    "        lw x7, 0(x5)         # x7 = count = 0",
    "        lw x8, 0(x6)         # x8 = limit = 5000",
    "",
    "loop:",
    "        #-------------------------------------------------",
    "        # Cuerpo del bucle: cada iteración implica un salto",
    "        #-------------------------------------------------",
    "        addi x7, x7, 1       # count++",
    "        sw x7, 0(x5)         # Guardar en memoria (1 acceso write)",
    "",
    "        # Condicional: si count < limit → saltar a loop",
    "        blt x7, x8, loop     # Branch condicional (salto)",
    "        addi x0, x0, 0       # NOP para evitar hazard de control (si no hay hardware)",
    "",
    "        # Si no se cumple, continúa aquí",
    "end:",
    "        # Salto incondicional final",
    "        jal x0, done         # Jump sin retorno (salto absoluto)",
    "        addi x0, x0, 0       # NOP (evita usar PC incorrecto si no hay branch forwarding)",
    "",
    "done:",
    "        # Fin del programa",
    "        nop                  # No operation (última instrucción)"
]



claseProc = ProcessorSimulator(riscv_code)
claseProc.run()