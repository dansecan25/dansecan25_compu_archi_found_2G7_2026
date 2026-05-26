
from .latencias_config import get_stage_latency, get_instruction_latency

class Execute():
    def __init__(self, mem_data=None):
        self.instruccionEjecutando = ""
        self.params = []
        self.ciclos_restantes = 0
        self.ocupada = False
        self.latencia_base = get_stage_latency('Execute')
        self.mem_data = mem_data if mem_data is not None else None  # Referencia a memoria de datos para lw

    def cargarInstruccion(self, instruccion, params):
        """Carga una instrucción si la etapa está libre y ejecuta la ALU."""
        if not self.ocupada:
            self.instruccionEjecutando = instruccion
            self.ciclos_restantes = get_instruction_latency(instruccion.split()[0] if instruccion else 'nop')
            self.ocupada = True
            
            # Ejecutar la ALU usando los params de RegisterFile
            resultado_params = []
            try:
                if not params:
                    resultado_params = []
                else:
                    accion = params[0]
                    if accion == 'nop':
                        resultado_params = ['nop']
                        print(f"[EXECUTE] NOP detectado, latencia={self.ciclos_restantes} ciclos")
                    elif accion == 'alu_op':
                        # Estructura: ['alu_op', opcode, rd, rs1, rs2, val_rs1, val_rs2]
                        opcode, rd, rs1, rs2, val_rs1, val_rs2 = params[1:]
                        if opcode == 'add': resultado = val_rs1 + val_rs2
                        elif opcode == 'sub': resultado = val_rs1 - val_rs2
                        elif opcode == 'mul': resultado = val_rs1 * val_rs2
                        elif opcode == 'div': resultado = val_rs1 // val_rs2 if val_rs2 != 0 else 0
                        elif opcode == 'xor': resultado = val_rs1 ^ val_rs2
                        elif opcode == 'and': resultado = val_rs1 & val_rs2
                        elif opcode == 'or': resultado = val_rs1 | val_rs2
                        elif opcode == 'slt': resultado = 1 if val_rs1 < val_rs2 else 0
                        else: resultado = 0
                        # Pasar a Store: ['reg_write', rd, resultado]
                        resultado_params = ['reg_write', rd, resultado]
                        print(f"[EXECUTE] ALU: {opcode} x{rd} = {val_rs1} {opcode} {val_rs2} = {resultado}, latencia={self.ciclos_restantes} ciclos")
                        
                    elif accion == 'alu_op_imm':
                        # Estructura: ['alu_op_imm', 'addi', rd, rs1, imm, val_rs1]
                        opcode, rd, rs1, imm, val_rs1 = params[1:]
                        resultado = val_rs1 + imm
                        resultado_params = ['reg_write', rd, resultado]
                        print(f"[EXECUTE] ALU: {opcode} x{rd} = {val_rs1} + {imm} = {resultado}, latencia={self.ciclos_restantes} ciclos")
                        
                    elif accion == 'mem_read':
                        # Estructura: ['mem_read', rd, rs1, offset, val_rs1]
                        rd, rs1, offset, val_rs1 = params[1:]
                        # Calcular dirección (no se lee memoria aún, se hace en Store)
                        addr = val_rs1 + offset
                        resultado_params = ['mem_read_and_reg_write', rd, addr]
                        print(f"[EXECUTE] ADDR_CALC (lw): addr = x{rs1}({val_rs1}) + {offset} = {addr}, latencia={self.ciclos_restantes} ciclos")
                        
                    elif accion == 'mem_write':
                        # Estructura: ['mem_write', rs2, rs1, offset, val_rs1, val_rs2]
                        rs2, rs1, offset, val_rs1, val_rs2 = params[1:]
                        # Calcular dirección
                        addr = val_rs1 + offset
                        resultado_params = ['mem_write', addr, val_rs2]
                        print(f"[EXECUTE] ADDR_CALC (sw): addr = x{rs1}({val_rs1}) + {offset} = {addr}, val = x{rs2}({val_rs2}), latencia={self.ciclos_restantes} ciclos")
                    
                    elif accion == 'branch':
                        # Estructura: ['branch', tipo, rs1, rs2, val_rs1, val_rs2, label_or_offset]
                        tipo, rs1, rs2, val_rs1, val_rs2, label_or_offset = params[1:]
                        
                        # Evaluar condición
                        branch_taken = False
                        if tipo == 'beq':
                            branch_taken = (val_rs1 == val_rs2)
                        
                        # Pasar info a Store (para actualizar PC si se toma)
                        resultado_params = ['branch_result', branch_taken, label_or_offset]
                        print(f"[EXECUTE] Branch {tipo}: x{rs1}({val_rs1}) vs x{rs2}({val_rs2}), taken={branch_taken}, target={label_or_offset}, latencia={self.ciclos_restantes} ciclos")
                    
                    elif accion == 'jump':
                        # Estructura: ['jump', tipo, rd, label]
                        tipo, rd, label = params[1:]
                        # jal siempre salta (incondicional) y guarda PC+1 en rd
                        # Pasar a Store: ['jump_result', rd, label]
                        resultado_params = ['jump_result', rd, label]
                        print(f"[EXECUTE] Jump {tipo}: rd=x{rd}, target={label}, latencia={self.ciclos_restantes} ciclos")
                        
                    else:
                        resultado_params = []
                        
            except Exception as e:
                print(f"[EXECUTE] Error ejecutando {instruccion}: {e}")
                resultado_params = []
            
            # Guardar params de resultado para pasarlos a Store
            self.params = resultado_params
            
            if instruccion:
                print(f"[EXECUTE] Ejecutando en ALU: {instruccion}, latencia={self.ciclos_restantes} ciclos")

    def tick(self):
        """Reduce un ciclo. Retorna True si la etapa completó su instrucción."""
        if self.ocupada and self.ciclos_restantes > 0:
            self.ciclos_restantes -= 1
            if self.ciclos_restantes == 0:
                self.ocupada = False
                return True
        return False

    def esta_libre(self):
        """Retorna True si la etapa puede recibir una nueva instrucción."""
        return not self.ocupada

    def getInstruccion(self):
        """Retorna la instrucción completada cuando está lista."""
        return self.instruccionEjecutando if not self.ocupada else ""

    def get_instruccion_actual(self):
        """Retorna la instrucción que se está procesando (aunque no esté completa)."""
        return self.instruccionEjecutando

    def get_estado(self):
        """Retorna string con estado actual para logging."""
        if self.ocupada:
            return f"Procesando: {self.instruccionEjecutando} ({self.ciclos_restantes} ciclos restantes)"
        else:
            return "Libre"