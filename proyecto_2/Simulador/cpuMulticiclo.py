"""
CPU Multiciclo (Multi-Cycle) - Procesador RISC-V
Ejecuta cada instrucción en múltiples ciclos de reloj.
Cada etapa (Fetch, Decode, Execute, Memory, Writeback) toma uno o más ciclos.

Ciclos por instrucción:
- Tipo R (add, sub): 4 ciclos (Fetch, Decode, Execute, Writeback)
- Tipo I (addi, lw): 5 ciclos (Fetch, Decode, Execute, Memory, Writeback)
- Store (sw): 4 ciclos (Fetch, Decode, Execute, Memory)
- Branch (beq, blt): 3 ciclos (Fetch, Decode, Execute)
- Jump (jal): 3 ciclos (Fetch, Decode, Execute)
"""

import sys
from pathlib import Path
import time

# Asegurar que el directorio Simulador esté en el path
sys.path.insert(0, str(Path(__file__).parent))

from componentes import ALU, BancoRegistros, Memoria, SignExtender
from control import UnidadControl

class CPUMulticiclo:
    def __init__(self):
        # Componentes del procesador
        self.mem_inst = Memoria(64)
        self.mem_data = Memoria(256)
        self.regs = BancoRegistros()
        self.alu = ALU()
        self.uc = UnidadControl()
        self.sign_ext = SignExtender()
        
        # Estado del procesador
        self.PC = 0
        self.labels = {}
        self.data_pointer = 0
        self.ciclo_actual = 0
        self.tiempo_inicio = 0
        self.instrucciones_ejecutadas = 0
        
        # Estado de la instrucción actual
        self.etapa_actual = "IDLE"  # IDLE, FETCH, DECODE, EXECUTE, MEMORY, WRITEBACK
        self.ciclos_en_etapa = 0
        self.instruccion_actual = ""
        self.IR = ""  # Instruction Register
        self.A = 0    # Registro temporal A
        self.B = 0    # Registro temporal B
        self.ALUOut = 0  # Resultado de ALU
        self.MDR = 0  # Memory Data Register
        self.opcode = ""
        self.rd = 0
        self.rs1 = 0
        self.rs2 = 0
        self.imm: int | str = 0  # Puede ser int (offset) o str (label)
        self.señales = {}
        
        # Log - Guardar en directorio Front
        log_dir = Path(__file__).parent.parent / "Front"
        log_path = log_dir / "log_multiciclo.txt"
        self.log_file = open(log_path, "w", encoding="utf-8")
        self.log_file.write("=== LOG DE EJECUCIÓN DEL CPU MULTICICLO ===\n")
        self.log_file.write("Arquitectura: Multi-Cycle (3-5 ciclos por instrucción)\n")
        self.log_file.write("Etapas: FETCH → DECODE → EXECUTE → MEMORY → WRITEBACK\n")
        self.log_file.write("=" * 80 + "\n\n")

    def log(self, mensaje):
        """Escribe un mensaje en el archivo de log."""
        self.log_file.write(mensaje + "\n")

    def cargarCodigo(self, codigo):
        """Carga el código RISC-V en memoria de instrucciones."""
        self.PC = 0
        self.mem_inst.data = [0] * len(self.mem_inst.data)
        self.labels = {}
        self.data_pointer = 0
        self.ciclo_actual = 0
        self.instrucciones_ejecutadas = 0
        self.etapa_actual = "IDLE"

        write_index = 0
        in_data_section = False
        in_text_section = False

        for instr in codigo:
            line = instr.strip()

            if line == "" or line.startswith("#"):
                continue

            if line == ".data":
                in_data_section = True
                in_text_section = False
                continue

            if line == ".text":
                in_text_section = True
                in_data_section = False
                continue

            if in_data_section:
                if ":" in line:
                    label, rest = line.split(":", 1)
                    label = label.strip()
                    rest = rest.strip()
                    self.labels[label] = self.data_pointer

                    if rest.startswith(".word"):
                        tokens = rest.split()
                        value = int(tokens[1])
                        self.mem_data.escribir(self.data_pointer, value)
                        self.data_pointer += 1
                    elif rest.startswith(".string"):
                        text = rest.split(" ", 1)[1].strip().strip("\"")
                        for ch in text:
                            self.mem_data.escribir(self.data_pointer, ord(ch))
                            self.data_pointer += 1
                    continue

            if line.endswith(":"):
                label = line[:-1]
                self.labels[label] = write_index
                continue

            self.mem_inst.escribir(write_index, line)
            write_index += 1

        self.log(f"{write_index} instrucciones cargadas")
        self.log(f"Labels detectados: {self.labels}\n")

    def ejecutar(self):
        """Ejecuta todas las instrucciones del programa."""
        self.tiempo_inicio = time.time()
        self.log("=== INICIANDO EJECUCIÓN ===\n")
        self.etapa_actual = "FETCH"
        
        while self.ejecutar_ciclo():
            pass
        
        tiempo_total = time.time() - self.tiempo_inicio
        cpi = self.ciclo_actual / self.instrucciones_ejecutadas if self.instrucciones_ejecutadas > 0 else 0
        
        self.log(f"\n{'='*80}")
        self.log(f"[EJECUCIÓN COMPLETADA]")
        self.log(f"Total de ciclos: {self.ciclo_actual}")
        self.log(f"Instrucciones ejecutadas: {self.instrucciones_ejecutadas}")
        self.log(f"Tiempo de ejecución: {tiempo_total:.6f} segundos")
        self.log(f"CPI (Cycles Per Instruction): {cpi:.2f}")
        self.log(f"{'='*80}\n")
        
        try:
            self.guardar_memoria_en_archivo("memoria_salida_multiciclo.txt")
        except Exception:
            pass
        
        self.log_file.close()

    def ejecutar_ciclo(self):
        """Ejecuta un ciclo de reloj (una etapa de una instrucción)."""
        self.ciclo_actual += 1
        
        if self.etapa_actual == "FETCH":
            return self.etapa_fetch()
        elif self.etapa_actual == "DECODE":
            return self.etapa_decode()
        elif self.etapa_actual == "EXECUTE":
            return self.etapa_execute()
        elif self.etapa_actual == "MEMORY":
            return self.etapa_memory()
        elif self.etapa_actual == "WRITEBACK":
            return self.etapa_writeback()
        else:
            return False

    def etapa_fetch(self):
        """Etapa FETCH: Lee la instrucción de memoria."""
        self.log(f"\n[CICLO {self.ciclo_actual}] FETCH - PC={self.PC}")
        
        instr_original = self.mem_inst.leer(self.PC)
        if not instr_original or not isinstance(instr_original, str):
            self.log(f"  Fin del programa")
            return False

        self.IR = instr_original.split("#")[0].strip()
        if self.IR == "":
            self.PC += 1
            return True

        self.instruccion_actual = self.IR
        self.log(f"  IR ← Mem[{self.PC}] = '{self.IR}'")
        
        # Avanzar a DECODE
        self.etapa_actual = "DECODE"
        return True

    def etapa_decode(self):
        """Etapa DECODE: Decodifica la instrucción y lee registros."""
        self.log(f"[CICLO {self.ciclo_actual}] DECODE")
        
        partes = self.IR.replace(",", "").split()
        self.opcode = partes[0]
        
        if self.opcode.startswith("."):
            self.log(f"  Directiva ignorada: {self.opcode}")
            self.PC += 1
            self.etapa_actual = "FETCH"
            return True

        if self.opcode == "nop":
            self.log(f"  NOP detectado")
            self.PC += 1
            self.etapa_actual = "FETCH"
            self.instrucciones_ejecutadas += 1
            return True

        self.señales = self.uc.decodificar(self.opcode)
        self.log(f"  Opcode: {self.opcode}")
        self.log(f"  Señales: {self.señales}")
        
        try:
            # Leer operandos según el tipo de instrucción
            if self.opcode in ["add", "sub"]:
                self.rd, self.rs1, self.rs2 = [int(p[1:]) for p in partes[1:4]]
                self.A = self.regs.leer(self.rs1)
                self.B = self.regs.leer(self.rs2)
                self.log(f"  A ← x{self.rs1} = {self.A}")
                self.log(f"  B ← x{self.rs2} = {self.B}")
                
            elif self.opcode == "addi":
                self.rd = int(partes[1][1:])
                self.rs1 = int(partes[2][1:])
                self.imm = int(partes[3])
                self.A = self.regs.leer(self.rs1)
                self.B = self.sign_ext.extender(self.imm)
                self.log(f"  A ← x{self.rs1} = {self.A}")
                self.log(f"  B ← SignExt({self.imm}) = {self.B}")
                
            elif self.opcode == "sw":
                self.rs2 = int(partes[1][1:])
                offset, reg = partes[2].split("(")
                offset_val = int(offset)
                self.imm = offset_val
                self.rs1 = int(reg[1:-1])
                self.A = self.regs.leer(self.rs1)
                self.B = self.regs.leer(self.rs2)
                self.log(f"  A ← x{self.rs1} = {self.A} (base)")
                self.log(f"  B ← x{self.rs2} = {self.B} (dato)")
                
            elif self.opcode == "lw":
                self.rd = int(partes[1][1:])
                offset, reg = partes[2].split("(")
                offset_val = int(offset)
                self.imm = offset_val
                self.rs1 = int(reg[1:-1])
                self.A = self.regs.leer(self.rs1)
                self.log(f"  A ← x{self.rs1} = {self.A} (base)")
                
            elif self.opcode in ["beq", "blt"]:
                self.rs1 = int(partes[1][1:])
                self.rs2 = int(partes[2][1:])
                self.imm = partes[3]  # label
                self.A = self.regs.leer(self.rs1)
                self.B = self.regs.leer(self.rs2)
                self.log(f"  A ← x{self.rs1} = {self.A}")
                self.log(f"  B ← x{self.rs2} = {self.B}")
                
            elif self.opcode == "jal":
                self.rd = int(partes[1][1:])
                self.imm = partes[2]  # label
                self.log(f"  Target: {self.imm}")
                
            elif self.opcode == "la":
                self.rd = int(partes[1][1:])
                self.imm = partes[2]  # label
                self.log(f"  Label: {self.imm}")
                
        except Exception as e:
            self.log(f"  ERROR en DECODE: {str(e)}")
            return False
        
        # Avanzar a EXECUTE
        self.etapa_actual = "EXECUTE"
        return True

    def etapa_execute(self):
        """Etapa EXECUTE: Ejecuta la operación ALU o calcula dirección."""
        self.log(f"[CICLO {self.ciclo_actual}] EXECUTE")
        
        try:
            if self.opcode in ["add", "sub"]:
                self.ALUOut = self.alu.operar(self.señales["ALUOp"], self.A, self.B)
                self.log(f"  ALUOut ← {self.A} {self.opcode} {self.B} = {self.ALUOut}")
                self.etapa_actual = "WRITEBACK"
                
            elif self.opcode == "addi":
                self.ALUOut = self.alu.operar("add", self.A, self.B)
                self.log(f"  ALUOut ← {self.A} + {self.B} = {self.ALUOut}")
                self.etapa_actual = "WRITEBACK"
                
            elif self.opcode in ["sw", "lw"]:
                # imm debe ser int para lw/sw (offset)
                offset = self.imm if isinstance(self.imm, int) else 0
                self.ALUOut = self.A + offset
                self.log(f"  ALUOut ← {self.A} + {offset} = {self.ALUOut} (dirección)")
                self.etapa_actual = "MEMORY"
                
            elif self.opcode == "beq":
                tomado = (self.A == self.B)
                self.log(f"  Comparación: {self.A} == {self.B} → {tomado}")
                if tomado:
                    if self.imm in self.labels:
                        self.PC = self.labels[self.imm]
                        self.log(f"  Branch TOMADO: PC ← {self.imm} ({self.PC})")
                    else:
                        self.log(f"  ERROR: Label '{self.imm}' no encontrado")
                else:
                    self.PC += 1
                    self.log(f"  Branch NO TOMADO: PC ← {self.PC}")
                self.etapa_actual = "FETCH"
                self.instrucciones_ejecutadas += 1
                
            elif self.opcode == "blt":
                tomado = (self.A < self.B)
                self.log(f"  Comparación: {self.A} < {self.B} → {tomado}")
                if tomado:
                    if self.imm in self.labels:
                        self.PC = self.labels[self.imm]
                        self.log(f"  Branch TOMADO: PC ← {self.imm} ({self.PC})")
                    else:
                        self.log(f"  ERROR: Label '{self.imm}' no encontrado")
                else:
                    self.PC += 1
                    self.log(f"  Branch NO TOMADO: PC ← {self.PC}")
                self.etapa_actual = "FETCH"
                self.instrucciones_ejecutadas += 1
                
            elif self.opcode == "jal":
                if self.imm in self.labels:
                    return_addr = self.PC + 1
                    self.regs.escribir(self.rd, return_addr)
                    self.PC = self.labels[self.imm]
                    self.log(f"  x{self.rd} ← {return_addr} (return address)")
                    self.log(f"  PC ← {self.imm} ({self.PC})")
                else:
                    self.log(f"  ERROR: Label '{self.imm}' no encontrado")
                self.etapa_actual = "FETCH"
                self.instrucciones_ejecutadas += 1
                
            elif self.opcode == "la":
                if self.imm in self.labels:
                    direccion = self.labels[self.imm]
                    self.regs.escribir(self.rd, direccion)
                    self.log(f"  x{self.rd} ← dirección({self.imm}) = {direccion}")
                    self.PC += 1
                else:
                    self.log(f"  ERROR: Label '{self.imm}' no encontrado")
                self.etapa_actual = "FETCH"
                self.instrucciones_ejecutadas += 1
                
            else:
                self.log(f"  ERROR: Instrucción '{self.opcode}' no implementada")
                return False
                
        except Exception as e:
            self.log(f"  ERROR en EXECUTE: {str(e)}")
            return False
        
        return True

    def etapa_memory(self):
        """Etapa MEMORY: Accede a memoria de datos (load/store)."""
        self.log(f"[CICLO {self.ciclo_actual}] MEMORY")
        
        try:
            if self.opcode == "lw":
                self.MDR = self.mem_data.leer(self.ALUOut)
                self.log(f"  MDR ← Mem[{self.ALUOut}] = {self.MDR}")
                self.etapa_actual = "WRITEBACK"
                
            elif self.opcode == "sw":
                self.mem_data.escribir(self.ALUOut, self.B)
                self.log(f"  Mem[{self.ALUOut}] ← {self.B}")
                self.PC += 1
                self.etapa_actual = "FETCH"
                self.instrucciones_ejecutadas += 1
                
        except Exception as e:
            self.log(f"  ERROR en MEMORY: {str(e)}")
            return False
        
        return True

    def etapa_writeback(self):
        """Etapa WRITEBACK: Escribe resultado en registro."""
        self.log(f"[CICLO {self.ciclo_actual}] WRITEBACK")
        
        try:
            if self.opcode in ["add", "sub", "addi"]:
                if self.señales.get("RegWrite", False):
                    self.regs.escribir(self.rd, self.ALUOut)
                    self.log(f"  x{self.rd} ← {self.ALUOut}")
                    
            elif self.opcode == "lw":
                self.regs.escribir(self.rd, self.MDR)
                self.log(f"  x{self.rd} ← {self.MDR}")
                
        except Exception as e:
            self.log(f"  ERROR en WRITEBACK: {str(e)}")
            return False
        
        self.PC += 1
        self.etapa_actual = "FETCH"
        self.instrucciones_ejecutadas += 1
        return True

    def guardar_memoria_en_archivo(self, ruta):
        """Guarda el contenido de la memoria de datos en un archivo."""
        mem_dir = Path(__file__).parent.parent / "Front"
        mem_path = mem_dir / ruta
        with open(mem_path, "w", encoding="utf-8") as f:
            for i, valor in enumerate(self.mem_data.data):
                f.write(f"[{i:03d}] -> {valor}\n")
        self.log(f"Estado de memoria escrito en {ruta}")

# Made with Bob
