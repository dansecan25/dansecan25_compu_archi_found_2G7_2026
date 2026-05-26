from componentes import ALU, BancoRegistros, Memoria, SignExtender, MUX
from control import UnidadControl
import os
from pathlib import Path

class CPU:
    def __init__(self):
        # Componentes
        self.mem_inst = Memoria(64)
        self.mem_data = Memoria(256)
        self.regs = BancoRegistros()
        self.alu = ALU()
        self.uc = UnidadControl()
        self.sign_ext = SignExtender()
        self.PC = 0
        self.labels = {}
        self.data_pointer = 0  # apunta dentro de memoria de datos


        # Log
        self.log_file = open("log.txt", "w", encoding="utf-8")
        self.log_file.write("=== LOG DE EJECUCIÓN DEL CPU ===\n")

    def log(self, mensaje):
        self.log_file.write(mensaje + "\n")

    def ejecutar(self, codigo):
        self.PC = 0
        self.mem_inst.data = [None] * len(self.mem_inst.data)
        self.labels = {}
        self.data_pointer = 0

        write_index = 0
        in_data_section = False
        in_text_section = False

        for instr in codigo:
            line = instr.strip()

            if line == "":
                continue
            if line.startswith("#"):
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

                    # Registrar dirección del label
                    self.labels[label] = self.data_pointer

                    # -------- .word --------
                    if rest.startswith(".word"):
                        tokens = rest.split()
                        value = int(tokens[1])  # solo el primer número
                        self.mem_data.escribir(self.data_pointer, value)
                        self.data_pointer += 1

                    # -------- .string --------
                    elif rest.startswith(".string"):
                        text = rest.split(" ", 1)[1]
                        text = text.strip().strip("\"")
                        for ch in text:
                            self.mem_data.escribir(self.data_pointer, ord(ch))
                            self.data_pointer += 1

                    continue
            # ============================
            # IGNORAR LABELS EN .text
            # ============================
            if line.endswith(":"): 
                # Guardar posición en instrucciones
                label = line[:-1]
                self.labels[label] = write_index
                continue

            # ============================
            # INSTRUCCIONES NORMALES
            # ============================
            self.mem_inst.escribir(write_index, line)
            write_index += 1

        self.log(f"{write_index} instrucciones cargadas")
        self.log(f"Labels detectados: {self.labels}")


    def guardar_memoria_en_archivo(self, ruta):
        with open(ruta, "w", encoding="utf-8") as f:
            for i, valor in enumerate(self.mem_data.data):
                f.write(f"[{i:03d}] -> {valor}\n")
        self.log(f"Estado de memoria escrito en {ruta}")

    def ejecutar_ciclo(self):
        instr_original = self.mem_inst.leer(self.PC)
        if not instr_original:
            self.log("Fin del programa")
            return False

        # LIMPIA COMENTARIOS ANTES DE TODO
        instr = instr_original.split("#")[0].strip()

        if instr == "":
            self.PC += 1
            return True

        self.log(f"\n=== Ciclo {self.PC} ===")
        self.log(f"Instrucción: {instr}")

        partes = instr.replace(",", "").split()
        opcode = partes[0]

        instrucciones_validas = ["add", "sub", "addi", "sw", "lw", "la", "jal", "nop", "blt", "beq"]

        # Directiva
        if opcode.startswith("."):
            self.log(f"Directiva ignorada: {opcode}")
            self.PC += 1
            return True

        if opcode not in instrucciones_validas:
            self.log(f"ERROR: La instrucción '{opcode}' no está implementada.")
            return False

        señales = self.uc.decodificar(opcode)
        self.log(f"Señales: {señales}")

        try:
            if opcode == "la":
                if len(partes) != 3:
                    raise ValueError("Cantidad incorrecta de parámetros")

                rd = int(partes[1][1:])
                label = partes[2]

                if label not in self.labels:
                    raise ValueError(f"Label '{label}' no encontrado")

                direccion = self.labels[label]
                self.regs.escribir(rd, direccion)
                self.log(f"la: x{rd} = dirección({label}) = {direccion}")

                self.PC += 1
                return True
            
            if opcode in ["add", "sub"]:
                if len(partes) != 4:
                    raise ValueError("Cantidad incorrecta de parámetros")

                rd, rs1, rs2 = [int(p[1:]) for p in partes[1:4]]
                a = self.regs.leer(rs1)
                b = self.regs.leer(rs2)
                res = self.alu.operar(señales["ALUOp"], a, b)

                if señales["RegWrite"]:
                    self.regs.escribir(rd, res)
                self.log(f"ALU: {a} {opcode} {b} = {res} → x{rd}")

            elif opcode == "addi":
                if len(partes) != 4:
                    raise ValueError("Cantidad incorrecta de parámetros")

                rd = int(partes[1][1:])
                rs1 = int(partes[2][1:])
                imm = int(partes[3])

                a = self.regs.leer(rs1)
                b = self.sign_ext.extender(imm)
                res = self.alu.operar("add", a, b)

                if señales["RegWrite"]:
                    self.regs.escribir(rd, res)
                self.log(f"ADDInmediato: x{rd} = {a} + {b} = {res}")

            elif opcode == "sw":
                if len(partes) != 3:
                    raise ValueError("Cantidad incorrecta de parámetros")

                rs2 = int(partes[1][1:])
                offset, reg = partes[2].split("(")
                offset = int(offset)
                rs1 = int(reg[1:-1])

                addr = self.regs.leer(rs1) + offset
                val = self.regs.leer(rs2)

                self.mem_data.escribir(addr, val)
                self.log(f"Store: Mem[{addr}] = x{rs2} valor guardado->({val})")

            elif opcode == "lw":
                if len(partes) != 3:
                    raise ValueError("Cantidad incorrecta de parámetros")

                rd = int(partes[1][1:])
                offset, reg = partes[2].split("(")
                offset = int(offset)
                rs1 = int(reg[1:-1])

                addr = self.regs.leer(rs1) + offset
                val = self.mem_data.leer(addr)

                self.regs.escribir(rd, val)
                self.log(f"Load: x{rd} = Mem[{addr}] = {val}")
            elif opcode == "nop":
                self.log("NOP: No se realiza ninguna operación.")
                self.PC += 1
                return True

            elif opcode == "jal":
                if len(partes) != 3:
                    raise ValueError("Cantidad incorrecta de parámetros")

                rd = int(partes[1][1:])
                label = partes[2]

                if label not in self.labels:
                    raise ValueError(f"Label '{label}' no encontrado")

                return_address = self.PC + 1
                self.regs.escribir(rd, return_address)

                self.log(f"jal: salto a {label}, x{rd}=retorno({return_address})")

                self.PC = self.labels[label]
                return True

            elif opcode == "la":
                if len(partes) != 3:
                    raise ValueError("Cantidad incorrecta de parámetros")

                rd = int(partes[1][1:])
                label = partes[2]

                if label not in self.labels:
                    raise ValueError(f"Label '{label}' no encontrado")

                direccion = self.labels[label]
                self.regs.escribir(rd, direccion)
                self.log(f"la: x{rd} = dirección({label}) = {direccion}")

                self.PC += 1
                return True

            elif opcode == "blt":
                if len(partes) != 4:
                    raise ValueError("Cantidad incorrecta de parámetros")

                rs1 = int(partes[1][1:])
                rs2 = int(partes[2][1:])
                label = partes[3]

                if label not in self.labels:
                    raise ValueError(f"Label '{label}' no encontrado")

                v1 = self.regs.leer(rs1)
                v2 = self.regs.leer(rs2)

                if v1 < v2:
                    self.log(f"blt: salto tomado → {label}")
                    self.PC = self.labels[label]
                else:
                    self.log(f"blt: no tomado")
                    self.PC += 1

                return True

            elif opcode == "beq":
                if len(partes) != 4:
                    raise ValueError("Cantidad incorrecta de parámetros")

                rs1 = int(partes[1][1:])
                rs2 = int(partes[2][1:])
                label = partes[3]

                if label not in self.labels:
                    raise ValueError(f"Label '{label}' no encontrado")

                v1 = self.regs.leer(rs1)
                v2 = self.regs.leer(rs2)

                if v1 == v2:
                    self.log(f"beq: salto tomado → {label}")
                    self.PC = self.labels[label]
                else:
                    self.log(f"beq: no tomado")
                    self.PC += 1

                return True

        except Exception as e:
            # ERRRO: instrucción válida pero parámetros inválidos
            self.log(f"ERROR: La instrucción '{opcode}' es válida, pero sus parámetros son incorrectos.")
            self.log(f"Detalle: {e}")
            return False

        # ============================
        # Continuar ejecución normal
        # ============================
        self.PC += 1
        self.log(f"PC → {self.PC}")
        return True

    def ejecutar_todo(self):
        while self.ejecutar_ciclo():
            pass
        self.log("\n--- EJECUCIÓN FINALIZADA ---")
        self.guardar_memoria_en_archivo("memoria_salida.txt")
        self.log_file.close()