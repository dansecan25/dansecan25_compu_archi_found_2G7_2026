from pipelineEtapas import EtapaStore, Fetch, RegisterFile, Execute, Decode
from proyecto_2.Simulador.componentes import Memoria
from proyecto_2.Simulador.control import UnidadControl
import os
from pathlib import Path
from proyecto_2.Simulador.cpuPipelineConPredicciondeSaltos import BranchPredictor
pathGen=((os.getcwd()).replace('\\','/'))+"/"

class CPUPipelinePrediccionSaltosHazardControl:
    def __init__(self, predictor_strategy='always_taken'):
        # Componentes del Pipeline
        self.mem_inst = Memoria(64)
        self.mem_data = Memoria(256)
        # Banco de registros simple para la simulación pipelined
        self.regs = [0] * 32
        self.etapa_fetch = Fetch()
        self.etapa_decode = Decode()
        self.etapa_registerFile = RegisterFile(regs=self.regs)
        self.etapa_execute = Execute(mem_data=self.mem_data)
        self.etapa_store = EtapaStore()
        
        # *** NUEVO: Branch Predictor ***
        self.branch_predictor = BranchPredictor(strategy=predictor_strategy)
        
        self.PC = 0
        self.labels = {}
        self.data_pointer = 0
        self.codigo = []
        self.instrucciones_cola = []
        self.indice_instruccion = 0
        self.ciclo_actual = 0
        
        # Tracking de branches especulativos
        self.speculative_branch_pc = None  # PC del branch en ejecución especulativa
        self.speculative_target = None     # Target predicho
        self.is_speculative = False        # ¿Estamos en modo especulativo?
        
        # Estadísticas
        self.total_flushes = 0
        self.branch_count = 0
        
        # Log
        self.log_file = open(pathGen+"log_prediccion_hazard_control.txt", "w", encoding="utf-8")
        self.log_file.write("=== LOG DE EJECUCIÓN DEL CPU PIPELINE CON PREDICCIÓN DE SALTOS ===\n")
        self.log_file.write(f"Estrategia de predicción: {predictor_strategy}\n")
        self.log_file.write("=" * 80 + "\n\n")

    def log(self, mensaje):
        print(mensaje)
        self.log_file.write(mensaje + "\n")

    def controlar_hazards(self, codigo: list[str]) -> list[str]:
        """
        Inserta NOPs en la lista de instrucciones para garantizar que
        cualquier consumidor de un registro 'rd' no llegue a su etapa
        RegisterFile antes de que el productor haya completado su Store.

        Se calcula la distancia mínima en instrucciones usando la latencia
        de Execute de la instrucción productora:
            required_gap = exec_latency + 2
        Si la distancia actual entre producer (i) y consumer (j) es menor,
        se insertan NOPs antes del consumer.

        Devuelve la nueva lista con NOPs insertados.
        """
        # import local para obtener latencias de instrucción
        from proyecto_2.Simulador.pipelineEtapas.latencias_config import get_instruction_latency

        def parse_regs(inst: str):
            """
            Extrae (opcode, rd, rs1, rs2) en forma normalizada:
            rd/rs1/rs2 devueltos como strings 'xN' o None.
            """
            if not inst:
                return None, None, None, None
            text = inst.split("#")[0].strip()
            if not text:
                return None, None, None, None
            parts = text.replace(",", " ").replace("(", " ").replace(")", " ").split()
            if not parts:
                return None, None, None, None
            op = parts[0]
            rd = rs1 = rs2 = None

            # R-type: add rd, rs1, rs2
            if op in ["add", "sub", "and", "or", "xor", "sll", "srl", "sra", "mul", "div", "rem", "slt"]:
                if len(parts) >= 4:
                    rd, rs1, rs2 = parts[1], parts[2], parts[3]

            # I-type arith: addi rd, rs1, imm
            elif op in ["addi", "andi", "ori", "xori", "slti", "sltiu"]:
                if len(parts) >= 3:
                    rd, rs1 = parts[1], parts[2]

            # loads: lw rd, offset(rs1)
            elif op == "lw":
                if len(parts) >= 3:
                    rd = parts[1]
                    # parts may be like ['lw','x4','0','x10'] after splitting parens
                    if len(parts) >= 4:
                        rs1 = parts[3]
                    else:
                        rs1 = parts[2]

            # stores: sw rs2, offset(rs1)
            elif op == "sw":
                if len(parts) >= 3:
                    rs2 = parts[1]
                    # base register after split parens
                    if len(parts) >= 4:
                        rs1 = parts[3]
                    else:
                        rs1 = parts[2]

            # branches use rs1, rs2
            elif op in ["beq", "bne", "blt", "bge", "bltu", "bgeu"]:
                if len(parts) >= 3:
                    rs1, rs2 = parts[1], parts[2]

            # jal rd, label
            elif op == "jal":
                if len(parts) >= 2:
                    rd = parts[1]

            # jalr rd, rs1, imm  (approx)
            elif op == "jalr":
                if len(parts) >= 3:
                    rd, rs1 = parts[1], parts[2]

            return op, rd, rs1, rs2

        nuevo: list[str] = []
        i = 0
        n = len(codigo)

        while i < n:
            inst = codigo[i]
            # siempre copiamos la instrucción actual (producer) al output;
            # si detectamos que hay que insertar nops antes de un consumidor
            # más adelante, lo haremos en el flujo de lookahead.
            nuevo.append(inst)

            op_i, rd_i, rs1_i, rs2_i = parse_regs(inst)
            # Si la instrucción no escribe un registro útil (rd None o x0), saltar lookahead.
            if rd_i is None or rd_i == "x0":
                i += 1
                continue

            # obtenemos la latencia de execute de la instrucción productora
            # si get_instruction_latency falla con el opcode, asumimos lat 1
            try:
                exec_lat = get_instruction_latency(op_i)
                if exec_lat is None:
                    exec_lat = 1
            except Exception:
                exec_lat = 1

            # required minimum gap in number of instructions between producer(i) and consumer(j)
            required_gap = exec_lat + 2  # derivado: j - i >= L + 2

            # mirar hacia adelante cada instrucción j y si encuentra un consumidor,
            # insertar la cantidad necesaria de NOPs *antes* del consumidor
            # (es decir, en la salida 'nuevo' entre lo que ya copié y la copia del consumidor).
            # Nota: si insertamos, tenemos que "copiar" las instrucciones intermedias ya leídas.
            look = 1
            inserted_total = 0
            while i + look < n:
                j = i + look
                inst_j = codigo[j]
                op_j, rd_j, rs1_j, rs2_j = parse_regs(inst_j)

                # si la instrucción j usa rd_i como rs1 o rs2 -> hazard detected
                uses_rd = (rs1_j == rd_i) or (rs2_j == rd_i)

                if uses_rd:
                    current_gap = look  # j - i
                    if current_gap < required_gap:
                        needed = required_gap - current_gap
                        # Insert 'needed' nops BEFORE the consumer (inst_j)
                        # But en 'nuevo' ya tenemos las producer y las instrucciones previas (hasta i),
                        # necesitamos migrar las instrucciones entre i+1 .. j-1 también a 'nuevo' before inserting nop,
                        # because we only appended inst (producer) so far. So append the intermediate ones now.
                        for k in range(1, look):
                            nuevo.append(codigo[i + k])
                            inserted_total += 0  # intermediate appended, not nops
                        # ahora insertamos los NOPs
                        for _ in range(needed):
                            nuevo.append("nop")
                        # ahora el consumidor (inst_j) será procesado en la próxima iteración del loop principal
                        # pero hemos avanzado la copia: necesitamos mover i to j (we'll skip the copied inters next)
                        i = j  # colocamos i en la posición del consumidor (estará copiada en próxima iteración)
                        break
                    else:
                        # no se necesita nop para este consumidor (la distancia ya es suficiente)
                        # no hacemos nada y continuamos buscando; pero si hay un consumidor, no necesitamos
                        # mirar consumidores más lejanos para el mismo rd (podrían existir, pero ya están a mayor gap)
                        break
                else:
                    # seguir mirando adelante
                    look += 1
                    continue

            else:
                # no se encontró consumidor en el futuro que use rd_i
                i += 1
                continue

            # si llegamos aquí, significa que hicimos un 'break' por haber insertado y pusimos i=j (consumer)
            # NO incrementamos i de otra forma (la próxima iteración copiará el consumer)
            # si el while look encontró uses_rd pero no necesitó insertar nop, no se modificó i y rompió -> incrementamos
            if i < n and codigo[i] == inst:
                # caso donde no avanzamos i arriba
                i += 1
            # si i fue puesto en j por el break, no incrementamos aquí (la siguiente iteración manejará consumer)

        # nota: el algoritmo anterior puede haber duplicado intermedios si no se cuida;
        # para mayor seguridad, normalizamos la salida: eliminamos secuencias superfluas de NOPs repetidos
        # pero evitando tocar la semántica. Esto es opcional; aquí lo dejamos tal cual.

        # debug simple
        if len(nuevo) > len(codigo):
            print(f"[HAZARD_CTRL] Se agregaron {len(nuevo)-len(codigo)} NOP(s). Nueva longitud: {len(nuevo)}")
        else:
            print("[HAZARD_CTRL] No se agregaron NOPs.")

        return nuevo




    def cargarCodigo(self, codigo:list[str]):
        """Carga el código (lista de instrucciones) en la cola."""
        self.codigo = []
        self.labels = {}
        for linea in codigo:
            linea = linea.split("#")[0].strip()
            if linea:
                if ':' in linea and not '(' in linea:
                    label_name = linea.split(':')[0].strip()
                    self.labels[label_name] = len(self.codigo) * 4
                    resto = linea.split(':', 1)[1].strip()
                    if resto:
                        self.codigo.append(resto)
                else:
                    self.codigo.append(linea)

        self.codigo=self.controlar_hazards(self.codigo)
        self.instrucciones_cola = self.codigo.copy()
        
        for i, instr in enumerate(self.instrucciones_cola):
            try:
                self.mem_inst.escribir(i, instr)
            except Exception:
                pass
        
        try:
            self.log(f"{len(self.instrucciones_cola)} instrucciones cargadas desde lista `riscv_code`")
            for idx, ins in enumerate(self.instrucciones_cola):
                self.log(f"  [{idx:03d}] {ins}")
        except Exception:
            pass

    def mostrar_estado_pipeline(self):
        """Imprime el estado actual de todas las etapas."""
        estado = f"\n[CICLO {self.ciclo_actual:3d}] [PC={self.indice_instruccion:3d}]"
        if self.is_speculative:
            estado += " [ESPECULATIVO]"
        estado += " Estado del Pipeline:\n"
        estado += f"  Fetch:        {self.etapa_fetch.get_estado()}\n"
        estado += f"  Decode:       {self.etapa_decode.get_estado()}\n"
        estado += f"  RegFile:      {self.etapa_registerFile.get_estado()}\n"
        estado += f"  Execute:      {self.etapa_execute.get_estado()}\n"
        estado += f"  Store:        {self.etapa_store.get_estado()}\n"
        return estado

    def _is_branch_instruction(self, instr):
        """Detecta si una instrucción es un branch."""
        if not instr:
            return False
        parts = instr.split()
        return len(parts) > 0 and parts[0] in ['beq']
    
    def _extract_branch_target(self, instr, current_pc):
        """Extrae el target de un branch (label o offset)."""
        parts = instr.replace(',', '').split()
        if len(parts) >= 4:
            target = parts[3]
            # Si es un label, resolverlo
            if target in self.labels:
                return self.labels[target]
            # Si es un offset numérico
            try:
                offset = int(target)
                return current_pc + offset * 4
            except:
                pass
        return None

    def tick(self):
        """
        Simula un ciclo de reloj con predicción de saltos.
        """
        # 1. Tick en todas las etapas
        self.etapa_fetch.tick()
        self.etapa_decode.tick()
        self.etapa_registerFile.tick()
        self.etapa_execute.tick()
        self.etapa_store.tick()

        # 2. Store → Writeback (procesamiento de resultados)
        if self.etapa_store.getInstruccion() != "":
            instr_store = self.etapa_store.get_instruccion_actual()
            self.log(f"[CICLO {self.ciclo_actual}] [COMPLETADA] {instr_store}")
            
            try:
                params = getattr(self.etapa_store, 'params', []) or []
                if params:
                    accion = params[0]
                    
                    if accion == 'reg_write':
                        rd, val = params[1], params[2]
                        if 0 <= rd < len(self.regs):
                            self.regs[rd] = val
                            self.log(f"[STORE] Registro x{rd} <- {val}")
                    
                    elif accion == 'mem_write':
                        addr, val = params[1], params[2]
                        try:
                            self.mem_data.escribir(addr, val)
                            self.log(f"[STORE] Mem[{addr}] <- {val}")
                        except Exception:
                            self.log(f"[STORE] Error escribiendo Mem[{addr}]")
                    
                    elif accion == 'mem_read_and_reg_write':
                        rd, addr = params[1], params[2]
                        val = self.mem_data.leer(addr)
                        if 0 <= rd < len(self.regs):
                            self.regs[rd] = val
                            self.log(f"[STORE] Load: x{rd} <- Mem[{addr}] = {val}")
                    
                    elif accion == 'branch_result':
                        # *** PROCESAMIENTO DE BRANCH CON PREDICCIÓN ***
                        self.branch_count += 1
                        branch_taken, label_or_offset = params[1], params[2]
                        
                        # Calcular PC real del branch
                        branch_pc = self.speculative_branch_pc if self.speculative_branch_pc else 0
                        
                        # Determinar target real
                        if branch_taken:
                            if label_or_offset in self.labels:
                                actual_target = self.labels[label_or_offset]
                            else:
                                try:
                                    actual_target = branch_pc + int(label_or_offset) * 4
                                except:
                                    actual_target = branch_pc + 4
                        else:
                            actual_target = branch_pc + 4  # Secuencial
                        
                        # Verificar si la predicción fue correcta
                        if self.is_speculative:
                            # Determinar si predijimos "tomado"
                            predicted_taken = (self.speculative_target != (branch_pc + 4))
                            
                            # Verificar si la predicción del target fue correcta
                            # Comparamos el target real con el target predicho (guardado)
                            prediction_correct = (actual_target == self.speculative_target)
                            
                            # Actualizar predictor
                            self.branch_predictor.update(branch_pc, branch_taken, predicted_taken)
                            
                            if prediction_correct:
                                self.log(f"[STORE] Branch PREDICCIÓN CORRECTA: PC={branch_pc}, target={actual_target}")
                                # No hacer nada, seguir con ejecución especulativa
                            else:
                                # Misprediction: FLUSH y corregir PC
                                self.log(f"[STORE] Branch MISPREDICTION: predicho={self.speculative_target}, real={actual_target}")
                                self.log(f"[STORE] FLUSH pipeline y corregir PC: {self.indice_instruccion} -> {actual_target}")
                                
                                self.indice_instruccion = actual_target
                                self.total_flushes += 1
                                
                                # Flush pipeline
                                self.etapa_fetch.instruccionEjecutando = ""
                                self.etapa_fetch.ocupada = False
                                self.etapa_decode.instruccionEjecutando = ""
                                self.etapa_decode.ocupada = False
                                self.etapa_registerFile.instruccionEjecutando = ""
                                self.etapa_registerFile.ocupada = False
                                self.etapa_execute.instruccionEjecutando = ""
                                self.etapa_execute.ocupada = False
                            
                            # Salir del modo especulativo
                            self.is_speculative = False
                            self.speculative_branch_pc = None
                            self.speculative_target = None
                        else:
                            # Branch sin predicción previa (no debería pasar normalmente)
                            self.log(f"[STORE] Branch procesado sin predicción previa")
                            if branch_taken:
                                self.indice_instruccion = actual_target
                    
                    elif accion == 'jump_result':
                        # JAL - siempre se toma (no necesita predicción, es incondicional)
                        rd, label = params[1], params[2]
                        
                        instr_actual = self.etapa_store.get_instruccion_actual()
                        pc_jal = -1
                        for i, instr in enumerate(self.codigo):
                            if instr == instr_actual:
                                pc_jal = i * 4
                                break
                        
                        if 0 < rd < len(self.regs) and pc_jal >= 0:
                            return_addr = pc_jal + 4
                            self.regs[rd] = return_addr
                            self.log(f"[STORE] JAL: x{rd} <- {return_addr} (return address)")
                        
                        if label in self.labels:
                            nuevo_pc = self.labels[label]
                        else:
                            try:
                                nuevo_pc = pc_jal + int(label) * 4
                            except:
                                nuevo_pc = pc_jal + 4
                        
                        self.log(f"[STORE] JAL: PC = {pc_jal} -> {nuevo_pc}")
                        self.indice_instruccion = nuevo_pc
                        
                        # Flush pipeline
                        self.etapa_fetch.instruccionEjecutando = ""
                        self.etapa_fetch.ocupada = False
                        self.etapa_decode.instruccionEjecutando = ""
                        self.etapa_decode.ocupada = False
                        self.etapa_registerFile.instruccionEjecutando = ""
                        self.etapa_registerFile.ocupada = False
                        self.etapa_execute.instruccionEjecutando = ""
                        self.etapa_execute.ocupada = False
                        self.log(f"[STORE] Pipeline flushed (JAL)")
            except Exception:
                pass
            
            self.etapa_store.instruccionEjecutando = ""
            self.etapa_store.ocupada = False

        # Execute → Store
        if self.etapa_execute.getInstruccion() != "" and self.etapa_store.esta_libre():
            instr = self.etapa_execute.getInstruccion()
            params = getattr(self.etapa_execute, 'params', []) or []
            
            self.etapa_store.cargarInstruccion(instr, params)
            self.etapa_execute.instruccionEjecutando = ""
            self.etapa_execute.ocupada = False

        # RegisterFile → Execute
        if self.etapa_registerFile.getInstruccion() != "" and self.etapa_execute.esta_libre():
            instr = self.etapa_registerFile.getInstruccion()
            params = getattr(self.etapa_registerFile, 'params', []) or []
            self.etapa_execute.cargarInstruccion(instr, params)
            self.etapa_registerFile.instruccionEjecutando = ""
            self.etapa_registerFile.ocupada = False

        # Decode → RegisterFile (*** AQUÍ DETECTAMOS BRANCHES ***)
        if self.etapa_decode.getInstruccion() != "" and self.etapa_registerFile.esta_libre():
            instr = self.etapa_decode.getInstruccion()
            
            # Obtener el PC guardado en params de Decode
            params_decode = getattr(self.etapa_decode, 'params', []) or []
            branch_pc = params_decode[0] if len(params_decode) > 0 else self.indice_instruccion - 12
            
            # *** PREDICCIÓN DE BRANCH ***
            if self._is_branch_instruction(instr):
                # Hacer predicción
                prediction = self.branch_predictor.predict(branch_pc, is_branch=True)
                
                if prediction:
                    # Predicción: TOMADO
                    target = self._extract_branch_target(instr, branch_pc)
                    if target:
                        self.log(f"[DECODE] Branch detectado: {instr} (PC={branch_pc})")
                        self.log(f"[DECODE] PREDICCIÓN: TOMADO -> target={target}")
                        
                        # Entrar en modo especulativo
                        self.is_speculative = True
                        self.speculative_branch_pc = branch_pc
                        self.speculative_target = target
                        
                        # Cambiar PC especulativamente
                        # NOTA: NO hacemos flush aquí, solo cambiamos PC
                        # Las instrucciones ya en pipeline continúan
                        self.indice_instruccion = target
                    else:
                        self.log(f"[DECODE] Branch detectado pero no se pudo extraer target")
                else:
                    # Predicción: NO TOMADO
                    self.log(f"[DECODE] Branch detectado: {instr} (PC={branch_pc})")
                    self.log(f"[DECODE] PREDICCIÓN: NO TOMADO (continuar secuencial)")
                    
                    self.is_speculative = True
                    self.speculative_branch_pc = branch_pc
                    # Target secuencial es PC del branch + 4
                    self.speculative_target = branch_pc + 4
            
            self.etapa_registerFile.cargarInstruccion(instr)
            self.etapa_decode.instruccionEjecutando = ""
            self.etapa_decode.ocupada = False

        # Fetch → Decode
        if self.etapa_fetch.getInstruccion() != "" and self.etapa_decode.esta_libre():
            instr = self.etapa_fetch.getInstruccion()
            # Pasar el PC guardado en params de Fetch a Decode
            params_fetch = getattr(self.etapa_fetch, 'params', []) or []
            self.etapa_decode.cargarInstruccion(instr, params_fetch)
            self.etapa_fetch.instruccionEjecutando = ""
            self.etapa_fetch.ocupada = False

        # Cargar siguiente instrucción en Fetch
        if self.indice_instruccion < len(self.instrucciones_cola) * 4 and self.etapa_fetch.esta_libre():
            instr = self.instrucciones_cola[self.indice_instruccion // 4]
            # *** GUARDAR EL PC CON LA INSTRUCCIÓN ***
            current_pc = self.indice_instruccion
            self.etapa_fetch.cargarInstruccion(instr, [current_pc])
            self.indice_instruccion += 4

        self.ciclo_actual += 1

    def ejecutar(self):
        """Ejecuta el programa completo con predicción de saltos."""
        self.log("\n=== INICIANDO SIMULACIÓN DEL PIPELINE CON PREDICCIÓN DE SALTOS ===\n")
        
        ciclos_max = 1000
        
        while self.ciclo_actual < ciclos_max:
            self.log(self.mostrar_estado_pipeline())
            self.tick()
            
            if (self.indice_instruccion >= len(self.instrucciones_cola) * 4 and
                self.etapa_fetch.get_instruccion_actual() == "" and
                self.etapa_decode.get_instruccion_actual() == "" and
                self.etapa_registerFile.get_instruccion_actual() == "" and
                self.etapa_execute.get_instruccion_actual() == "" and
                self.etapa_store.get_instruccion_actual() == ""):
                break
        
        self.log("\n" + "=" * 80)
        self.log(f"[SIMULACIÓN COMPLETADA] Total de ciclos: {self.ciclo_actual}")
        self.log(f"[ESTADÍSTICAS DE PREDICCIÓN]")
        self.log(f"  Total branches: {self.branch_count}")
        self.log(f"  Predicciones: {self.branch_predictor.predictions}")
        self.log(f"  Correctas: {self.branch_predictor.correct_predictions}")
        self.log(f"  Incorrectas: {self.branch_predictor.mispredictions}")
        self.log(f"  Precisión: {self.branch_predictor.get_accuracy():.2f}%")
        self.log(f"  Total flushes: {self.total_flushes}")
        self.log("=" * 80 + "\n")
        
        try:
            self.guardar_memoria_en_archivo("memoria_salida_prediccion_hazard_control.txt")
        except Exception:
            pass
        self.log_file.close()

    def guardar_memoria_en_archivo(self, ruta):
        """Guarda el contenido de la memoria de datos en un archivo."""
        with open(pathGen+ruta, "w", encoding="utf-8") as f:
            for i, valor in enumerate(self.mem_data.data):
                f.write(f"[{i:03d}] -> {valor}\n")
        self.log(f"Estado de memoria escrito en {ruta}")