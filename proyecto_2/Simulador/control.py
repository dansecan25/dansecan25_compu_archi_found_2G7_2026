class UnidadControl:
    def __init__(self):
        self.control = {
            "RegWrite": 0,
            "ALUSrc": 0,
            "MemRead": 0,
            "MemWrite": 0,
            "MemToReg": 0,
            "Branch": 0,
            "ALUOp": "add"
        }

    def decodificar(self, opcode):

        # Reset de señales
        for key in self.control:
            self.control[key] = 0
        self.control["ALUOp"] = "add"

        # -------------------------
        # R-TYPE
        # -------------------------
        if opcode in ["add", "sub", "and", "or", "xor", "slt"]:
            self.control.update({
                "RegWrite": 1,
                "ALUSrc": 0,
                "MemToReg": 0,
                "ALUOp": opcode
            })

        # -------------------------
        # I-TYPE → addi
        # -------------------------
        elif opcode == "addi":
            self.control.update({
                "RegWrite": 1,
                "ALUSrc": 1,
                "ALUOp": "add"
            })

        # -------------------------
        # LOAD
        # -------------------------
        elif opcode == "lw":
            self.control.update({
                "RegWrite": 1,
                "ALUSrc": 1,
                "MemRead": 1,
                "MemToReg": 1
            })

        # -------------------------
        # STORE
        # -------------------------
        elif opcode == "sw":
            self.control.update({
                "ALUSrc": 1,
                "MemWrite": 1
            })

        # -------------------------
        # BRANCHES
        # -------------------------
        elif opcode == "beq":
            self.control.update({
                "Branch": 1,
                "ALUSrc": 0,
                "ALUOp": "sub"   # beq hace rs1 - rs2
            })

        elif opcode == "blt":
            self.control.update({
                "Branch": 1,
                "ALUSrc": 0,
                "ALUOp": "slt"   # comparar rs1 < rs2
            })

        # -------------------------
        # JAL (salto incondicional con link)
        # -------------------------
        elif opcode == "jal":
            self.control.update({
                "RegWrite": 1,  # rd recibe return address
                "Branch": 1     # salto incondicional
            })

        # -------------------------
        # LA (pseudo-instrucción)
        # No usa señales de CPU porque se ejecuta por software
        # -------------------------
        elif opcode == "la":
            self.control.update({
                "RegWrite": 1   # rd recibe dirección
            })

        # -------------------------
        # NOP
        # -------------------------
        elif opcode == "nop":
            # No hace nada
            pass

        else:
            print(f"[UnidadControl] Opcode desconocido: {opcode}")

        return self.control