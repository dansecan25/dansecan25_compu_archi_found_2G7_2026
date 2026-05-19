


from .latencias_config import get_stage_latency

class RegisterFile():
    def __init__(self, regs=None):
        self.instruccionEjecutando = ""
        self.params = []
        self.ciclos_restantes:int = 0
        self.ocupada:bool = False
        self.latencia = get_stage_latency('RegisterFile')
        self.regs = regs if regs is not None else [0] * 32  # Referencia al banco de registros

    def cargarInstruccion(self, instruccion):
        """Carga una instrucción si la etapa está libre y lee los operandos del banco de registros."""
        if not self.ocupada:
            self.instruccionEjecutando = instruccion
            self.ciclos_restantes = self.latencia
            self.ocupada = True
            
            # Parsear la instrucción y leer los operandos del banco de registros
            try:
                partes = instruccion.replace(',', '').split()
                opcode = partes[0] if partes else ''
                
                # Estructura: opcode rd rs1 rs2 / opcode rd rs1 imm / etc.
                if opcode == 'nop':
                    # NOP: no hace nada, params vacíos
                    self.params = ['nop']
                    print(f"[REGISTER_FILE] NOP detectado, latencia={self.latencia} ciclos")
                    
                elif opcode in ['add', 'sub', 'mul', 'div', 'xor', 'and', 'or', 'slt']:
                    # Format: add rd, rs1, rs2
                    rd = int(partes[1][1:]) if len(partes) > 1 else 0
                    rs1 = int(partes[2][1:]) if len(partes) > 2 else 0
                    rs2 = int(partes[3][1:]) if len(partes) > 3 else 0
                    val_rs1 = self.regs[rs1] if 0 <= rs1 < len(self.regs) else 0
                    val_rs2 = self.regs[rs2] if 0 <= rs2 < len(self.regs) else 0
                    # Pasar instrucción, opcode, rd, rs1, rs2, val_rs1, val_rs2 a Execute
                    self.params = ['alu_op', opcode, rd, rs1, rs2, val_rs1, val_rs2]
                    print(f"[REGISTER_FILE] Leyendo registros: {instruccion}, x{rs1}={val_rs1}, x{rs2}={val_rs2}, latencia={self.latencia} ciclos")
                    
                elif opcode == 'addi':
                    # Format: addi rd, rs1, imm
                    rd = int(partes[1][1:]) if len(partes) > 1 else 0
                    rs1 = int(partes[2][1:]) if len(partes) > 2 else 0
                    imm = int(partes[3]) if len(partes) > 3 else 0
                    val_rs1 = self.regs[rs1] if 0 <= rs1 < len(self.regs) else 0
                    self.params = ['alu_op_imm', 'addi', rd, rs1, imm, val_rs1]
                    print(f"[REGISTER_FILE] Leyendo registros: {instruccion}, x{rs1}={val_rs1}, imm={imm}, latencia={self.latencia} ciclos")
                    
                elif opcode == 'lw':
                    # Format: lw rd, offset(rs1)
                    rd = int(partes[1][1:]) if len(partes) > 1 else 0
                    offset_reg = partes[2] if len(partes) > 2 else '0(x0)'
                    offset, rs1 = offset_reg.split('(')
                    offset = int(offset)
                    rs1 = int(rs1[1:-1])
                    val_rs1 = self.regs[rs1] if 0 <= rs1 < len(self.regs) else 0
                    self.params = ['mem_read', rd, rs1, offset, val_rs1]
                    print(f"[REGISTER_FILE] Leyendo registros: {instruccion}, x{rs1}={val_rs1}, offset={offset}, latencia={self.latencia} ciclos")
                    
                elif opcode == 'sw':
                    # Format: sw rs2, offset(rs1)
                    rs2 = int(partes[1][1:]) if len(partes) > 1 else 0
                    offset_reg = partes[2] if len(partes) > 2 else '0(x0)'
                    offset, rs1 = offset_reg.split('(')
                    offset = int(offset)
                    rs1 = int(rs1[1:-1])
                    val_rs1 = self.regs[rs1] if 0 <= rs1 < len(self.regs) else 0
                    val_rs2 = self.regs[rs2] if 0 <= rs2 < len(self.regs) else 0
                    self.params = ['mem_write', rs2, rs1, offset, val_rs1, val_rs2]
                    print(f"[REGISTER_FILE] Leyendo registros: {instruccion}, x{rs1}={val_rs1}, x{rs2}={val_rs2}, offset={offset}, latencia={self.latencia} ciclos")
                
                elif opcode == 'beq':
                    # Format: beq rs1, rs2, label/offset
                    rs1 = int(partes[1][1:]) if len(partes) > 1 else 0
                    rs2 = int(partes[2][1:]) if len(partes) > 2 else 0
                    label_or_offset = partes[3] if len(partes) > 3 else '0'
                    val_rs1 = self.regs[rs1] if 0 <= rs1 < len(self.regs) else 0
                    val_rs2 = self.regs[rs2] if 0 <= rs2 < len(self.regs) else 0
                    self.params = ['branch', 'beq', rs1, rs2, val_rs1, val_rs2, label_or_offset]
                    print(f"[REGISTER_FILE] Branch: {instruccion}, x{rs1}={val_rs1}, x{rs2}={val_rs2}, target={label_or_offset}, latencia={self.latencia} ciclos")
                
                elif opcode == 'jal':
                    # Format: jal rd, label
                    rd = int(partes[1][1:]) if len(partes) > 1 else 0
                    label = partes[2] if len(partes) > 2 else '0'
                    # jal es salto incondicional, guarda PC+1 en rd
                    self.params = ['jump', 'jal', rd, label]
                    print(f"[REGISTER_FILE] Jump: {instruccion}, rd=x{rd}, target={label}, latencia={self.latencia} ciclos")
                    
                else:
                    # Instrucción desconocida o etiqueta
                    self.params = []
                    print(f"[REGISTER_FILE] Leyendo registros: {instruccion}, latencia={self.latencia} ciclos")
                    
            except Exception as e:
                self.params = []
                print(f"[REGISTER_FILE] Error parseando {instruccion}: {e}, latencia={self.latencia} ciclos")

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