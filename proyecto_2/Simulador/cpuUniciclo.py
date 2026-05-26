"""
CPU Uniciclo (Single-Cycle) - Procesador RISC-V
Ejecuta una instrucción completa en un solo ciclo de reloj.
Todas las etapas (Fetch, Decode, Execute, Memory, Writeback) ocurren en el mismo ciclo.
"""

import sys
from pathlib import Path
import time

# Asegurar que el directorio Simulador esté en el path
sys.path.insert(0, str(Path(__file__).parent))

from componentes import ALU, BancoRegistros, Memoria, SignExtender
from control import UnidadControl

class CPUUniciclo:
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
        
        # Log - Guardar en directorio Front
        log_dir = Path(__file__).parent.parent / "Front"
        log_path = log_dir / "log_uniciclo.txt"
        self.log_file = open(log_path, "w", encoding="utf-8")
        self.log_file.write("=== LOG DE EJECUCIÓN DEL CPU UNICICLO ===\n")
        self.log_file.write("Arquitectura: Single-Cycle (1 instrucción por ciclo)\n")
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
        
        while self.ejecutar_ciclo():
            pass
        
        tiempo_total = time.time() - self.tiempo_inicio
        self.log(f"\n{'='*80}")
        self.log(f"[EJECUCIÓN COMPLETADA]")
        self.log(f"Total de ciclos: {self.ciclo_actual}")
        self.log(f"Instrucciones ejecutadas: {self.instrucciones_ejecutadas}")
        self.log(f"Tiempo de ejecución: {tiempo_total:.6f} segundos")
        self.log(f"CPI (Cycles Per Instruction): 1.0 (arquitectura uniciclo)")
        self.log(f"{'='*80}\n")
        
        try:
            self.guardar_memoria_en_archivo("memoria_salida_uniciclo.txt")
        except Exception:
            pass
        
        self.log_file.close()

    def ejecutar_ciclo(self):
        """Ejecuta un ciclo completo (una instrucción completa)."""
        self.ciclo_actual += 1
        
        # FETCH: Leer instrucción de memoria
        instr_original = self.mem_inst.leer(self.PC)
        if not instr_original or not isinstance(instr_original, str):
            self.log(f"[CICLO {self.ciclo_actual}] Fin del programa (PC={self.PC})")
            return False

        instr = instr_original.split("#")[0].strip()
        if instr == "":
            self.PC += 1
            return True

        self.log(f"\n[CICLO {self.ciclo_actual}] PC={self.PC}")
        self.log(f"  Instrucción: {instr}")

        # DECODE: Decodificar instrucción
        partes = instr.replace(",", "").split()
        opcode = partes[0]

        if opcode.startswith("."):
            self.log(f"  Directiva ignorada: {opcode}")
            self.PC += 1
            return True

        if opcode == "nop":
            self.log(f"  NOP: No operation")
            self.PC += 1
            self.instrucciones_ejecutadas += 1
            return True

        señales = self.uc.decodificar(opcode)
        self.log(f"  Señales de control: {señales}")

        try:
            # EXECUTE, MEMORY, WRITEBACK: Ejecutar según el tipo de instrucción
            if opcode in ["add", "sub"]:
                rd, rs1, rs2 = [int(p[1:]) for p in partes[1:4]]
                a = self.regs.leer(rs1)
                b = self.regs.leer(rs2)
                res = self.alu.operar(señales["ALUOp"], a, b)
                if señales["RegWrite"]:
                    self.regs.escribir(rd, res)
                self.log(f"  ALU: x{rs1}({a}) {opcode} x{rs2}({b}) = {res} → x{rd}")

            elif opcode == "addi":
                rd = int(partes[1][1:])
                rs1 = int(partes[2][1:])
                imm = int(partes[3])
                a = self.regs.leer(rs1)
                b = self.sign_ext.extender(imm)
                res = self.alu.operar("add", a, b)
                if señales["RegWrite"]:
                    self.regs.escribir(rd, res)
                self.log(f"  ADDI: x{rs1}({a}) + {imm} = {res} → x{rd}")

            elif opcode == "sw":
                rs2 = int(partes[1][1:])
                offset, reg = partes[2].split("(")
                offset = int(offset)
                rs1 = int(reg[1:-1])
                addr = self.regs.leer(rs1) + offset
                val = self.regs.leer(rs2)
                self.mem_data.escribir(addr, val)
                self.log(f"  SW: Mem[{addr}] ← x{rs2}({val})")

            elif opcode == "lw":
                rd = int(partes[1][1:])
                offset, reg = partes[2].split("(")
                offset = int(offset)
                rs1 = int(reg[1:-1])
                addr = self.regs.leer(rs1) + offset
                val = self.mem_data.leer(addr)
                self.regs.escribir(rd, val)
                self.log(f"  LW: x{rd} ← Mem[{addr}]({val})")

            elif opcode == "la":
                rd = int(partes[1][1:])
                label = partes[2]
                if label not in self.labels:
                    raise ValueError(f"Label '{label}' no encontrado")
                direccion = self.labels[label]
                self.regs.escribir(rd, direccion)
                self.log(f"  LA: x{rd} ← dirección({label})={direccion}")

            elif opcode == "jal":
                rd = int(partes[1][1:])
                label = partes[2]
                if label not in self.labels:
                    raise ValueError(f"Label '{label}' no encontrado")
                return_address = self.PC + 1
                self.regs.escribir(rd, return_address)
                self.log(f"  JAL: x{rd} ← {return_address}, PC ← {label}")
                self.PC = self.labels[label]
                self.instrucciones_ejecutadas += 1
                return True

            elif opcode == "beq":
                rs1 = int(partes[1][1:])
                rs2 = int(partes[2][1:])
                label = partes[3]
                if label not in self.labels:
                    raise ValueError(f"Label '{label}' no encontrado")
                v1 = self.regs.leer(rs1)
                v2 = self.regs.leer(rs2)
                if v1 == v2:
                    self.log(f"  BEQ: x{rs1}({v1}) == x{rs2}({v2}) → TOMADO, PC ← {label}")
                    self.PC = self.labels[label]
                else:
                    self.log(f"  BEQ: x{rs1}({v1}) != x{rs2}({v2}) → NO TOMADO")
                    self.PC += 1
                self.instrucciones_ejecutadas += 1
                return True

            elif opcode == "blt":
                rs1 = int(partes[1][1:])
                rs2 = int(partes[2][1:])
                label = partes[3]
                if label not in self.labels:
                    raise ValueError(f"Label '{label}' no encontrado")
                v1 = self.regs.leer(rs1)
                v2 = self.regs.leer(rs2)
                if v1 < v2:
                    self.log(f"  BLT: x{rs1}({v1}) < x{rs2}({v2}) → TOMADO, PC ← {label}")
                    self.PC = self.labels[label]
                else:
                    self.log(f"  BLT: x{rs1}({v1}) >= x{rs2}({v2}) → NO TOMADO")
                    self.PC += 1
                self.instrucciones_ejecutadas += 1
                return True

            else:
                self.log(f"  ERROR: Instrucción '{opcode}' no implementada")
                return False

        except Exception as e:
            self.log(f"  ERROR: {str(e)}")
            return False

        self.PC += 1
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
