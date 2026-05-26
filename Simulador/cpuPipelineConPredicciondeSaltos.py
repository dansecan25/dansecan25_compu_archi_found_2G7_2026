from pipelineEtapas import EtapaStore, Fetch, RegisterFile, Execute, Decode
from componentes import Memoria
from control import UnidadControl
import os
from pathlib import Path
pathGen=((os.getcwd()).replace('\\','/'))+"/"


class BranchPredictor:
    """
    Predictor de saltos simple (Always Taken por defecto).
    Puede extenderse con otras estrategias.
    """
    def __init__(self, strategy='always_taken'):
        """
        strategy: 'always_taken', 'always_not_taken'
        """
        self.strategy = strategy
        
        # Estadísticas
        self.predictions = 0
        self.correct_predictions = 0
        self.mispredictions = 0
    
    def predict(self, pc, is_branch=True):
        """
        Predice si un branch será tomado.
        Retorna: True (tomado), False (no tomado)
        """
        if not is_branch:
            return False
        
        self.predictions += 1
        
        if self.strategy == 'always_taken':
            return True
        elif self.strategy == 'always_not_taken':
            return False
        
        return True  # Default: always taken
    
    def update(self, pc, actual_taken, predicted_taken):
        """
        Actualiza el predictor con el resultado real del branch.
        """
        if predicted_taken == actual_taken:
            self.correct_predictions += 1
        else:
            self.mispredictions += 1
    
    def get_accuracy(self):
        """Retorna la precisión del predictor."""
        if self.predictions == 0:
            return 0.0
        return (self.correct_predictions / self.predictions) * 100


class CPUpipelineConPrediccionSaltos:
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
        self.log_file = open(pathGen+"log_prediccion.txt", "w", encoding="utf-8")
        self.log_file.write("=== LOG DE EJECUCIÓN DEL CPU PIPELINE CON PREDICCIÓN DE SALTOS ===\n")
        self.log_file.write(f"Estrategia de predicción: {predictor_strategy}\n")
        self.log_file.write("=" * 80 + "\n\n")

    def log(self, mensaje):
        print(mensaje)
        self.log_file.write(mensaje + "\n")

    def cargarCodigo(self, codigo):
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
            self.guardar_memoria_en_archivo("memoria_salida_prediccion.txt")
        except Exception:
            pass
        self.log_file.close()

    def guardar_memoria_en_archivo(self, ruta):
        """Guarda el contenido de la memoria de datos en un archivo."""
        with open(pathGen+ruta, "w", encoding="utf-8") as f:
            for i, valor in enumerate(self.mem_data.data):
                f.write(f"[{i:03d}] -> {valor}\n")
        self.log(f"Estado de memoria escrito en {ruta}")