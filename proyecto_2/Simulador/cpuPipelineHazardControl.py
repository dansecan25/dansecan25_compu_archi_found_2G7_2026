from pipelineEtapas import EtapaStore, Fetch, RegisterFile, Execute, Decode
from componentes import Memoria
from control import UnidadControl
import os
from pathlib import Path

class CPUPipelineHazardControl:
    def __init__(self):
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
        self.PC:int = 0
        self.labels = {}
        self.data_pointer = 0
        self.codigo:list[str] = []
        self.instrucciones_cola:list[str] = []  # Cola de instrucciones a cargar en Fetch
        self.indice_instruccion:int = 0  # Índice de siguiente instrucción a cargar
        self.ciclo_actual:int = 0  # Contador de ciclos de reloj
        
        # Log - Ruta corregida para que el frontend lo encuentre
        log_dir = Path(__file__).parent.parent / "Front"
        log_path = log_dir / "log_hazard_control.txt"
        self.log_file = open(log_path, "w", encoding="utf-8")
        self.log_file.write("=== LOG DE EJECUCIÓN DEL CPU PIPELINE CON HAZARD CONTROL ===\n")
        self.log_file.write("Latencias: Fetch=1, Decode=1, RegisterFile=1, Execute=2(var), Store=1\n")
        self.log_file.write("=" * 80 + "\n\n")

    def log(self, mensaje):
        self.log_file.write(mensaje + "\n")
    
    def controlar_hazards(self, codigo: list[str]) -> list[str]:
        """
        Nuevo detector:
        - detecta RAW con distancia 1 y 2
        - para load-use: inserta 1 NOP antes del consumidor
        - para RAW normal: inserta 1 NOP antes del consumidor (ajustable)
        """
        def parse(inst):
            inst = inst.split("#")[0].strip()
            if not inst:
                return None, None, None, None
            parts = inst.replace(",", " ").replace("(", " ").replace(")", " ").split()
            op = parts[0]
            rd = rs1 = rs2 = None
            if op in ["add","sub","and","or","xor","sll","srl","sra","mul","div","rem"]:
                if len(parts) >= 4:
                    rd, rs1, rs2 = parts[1], parts[2], parts[3]
            elif op in ["addi","andi","ori","xori","slti","sltiu","li"]:
                if len(parts) >= 3:
                    rd, rs1 = parts[1], parts[2]
            elif op == "lw":
                if len(parts) >= 3:
                    rd = parts[1]; rs1 = parts[3] if len(parts) > 3 else None
            elif op == "sw":
                if len(parts) >= 3:
                    rs2 = parts[1]; rs1 = parts[3] if len(parts) > 3 else None
            elif op in ["beq","bne","blt","bge","bltu","bgeu"]:
                if len(parts) >= 3:
                    rs1, rs2 = parts[1], parts[2]
            elif op == "jal":
                if len(parts) >= 2:
                    rd = parts[1]
            elif op == "jalr":
                if len(parts) >= 3:
                    rd, rs1 = parts[1], parts[2]
            return rd, rs1, rs2, op

        out = []
        i = 0
        while i < len(codigo):
            inst = codigo[i]
            rd_i, rs1_i, rs2_i, op_i = parse(inst)
            # lookahead j = i+1 and i+2
            # We'll decide whether to insert NOPs BEFORE the consumer.
            inserted = False

            for j in (1, 2):  # check next 1 and 2 instructions
                if i + j >= len(codigo):
                    break
                rd_j, rs1_j, rs2_j, op_j = parse(codigo[i + j])
                if rd_i and rd_i != "x0":
                    # consumer uses rd_i?
                    if rs1_j == rd_i or rs2_j == rd_i:
                        # if producer is load, ensure one NOP before consumer
                        if op_i == "lw":
                            # insert one nop BEFORE consumer (i+j)
                            # append current inst, then inject nops to push consumer
                            out.append(inst)
                            # add (j-1) original instructions between producer and consumer
                            for k in range(1, j):
                                out.append(codigo[i+k])
                            out.append("nop")
                            # now advance i to skip what we already copied (producer + intermediate)
                            i += j
                            inserted = True
                            break
                        else:
                            # general RAW: insert one nop before consumer
                            out.append(inst)
                            for k in range(1, j):
                                out.append(codigo[i+k])
                            out.append("nop")
                            i += j
                            inserted = True
                            break
            if not inserted:
                out.append(inst)
                i += 1

        # optional debug print
        if len(out) > len(codigo):
            print("Se agregaron nops para manejar hazards. Nuevo tamaño:", len(out))
        return out




    """
    Funcion: Limpia las lineas de codigo y carga el codigo en self.codigo Los labels los almacena con su ubicación PC
    """
    def cargarCodigo(self, codigo:list[str]):
        # Filtrar comentarios y líneas vacías, detectar labels
        self.codigo = []
        self.labels = {} #{label:posicionPC}
        for linea in codigo:
            linea = linea.split("#")[0].strip()
            if linea:
                # Detectar labels (formato: "label:")
                if ':' in linea and not '(' in linea:  # Evitar confusión con offset(reg)
                    label_name = linea.split(':')[0].strip()
                    self.labels[label_name] = len(self.codigo) * 4  # PC en múltiplos de 4
                    # Si hay instrucción después del label en la misma línea
                    resto = linea.split(':', 1)[1].strip()
                    if resto:
                        self.codigo.append(resto)
                else:
                    self.codigo.append(linea)

        #Agarra self.codigo, antes de copiarlo, y lo revisa por hazards, si encuentra un hazard, agrega los nops despues de la instruccion con un potencial hazard
        self.codigo=self.controlar_hazards(self.codigo)


        self.instrucciones_cola = self.codigo.copy()
        # Escribir también en la memoria de instrucciones para compatibilidad
        # con el comportamiento anterior de `CPU.cargar_programa_desde_archivo`.
        #almacena el codigo en ubicaciones especificas en la memoria de instrucciones, donde van cada 4 posiciones
        for i, instr in enumerate(self.instrucciones_cola):
            try:
                self.mem_inst.escribir(i, instr)
            except Exception:
                # ignorar errores de escritura fuera de rango
                pass
        # Registrar en el log cuántas instrucciones se cargaron y listarlas

        #carga las instrucciones en el log
        try:
            self.log(f"{len(self.instrucciones_cola)} instrucciones cargadas desde lista `riscv_code`")
            for idx, ins in enumerate(self.instrucciones_cola):
                self.log(f"  [{idx:03d}] {ins}")
        except Exception:
            # si el log no está disponible por alguna razón, no interrumpir
            pass


    def mostrar_estado_pipeline(self):
        """Imprime el estado actual de todas las etapas."""
        estado = f"\n[CICLO {self.ciclo_actual:3d}] [PC={self.indice_instruccion:3d}] Estado del Pipeline:\n"
        estado += f"  Fetch:        {self.etapa_fetch.get_estado()}\n"
        estado += f"  Decode:       {self.etapa_decode.get_estado()}\n"
        estado += f"  RegFile:      {self.etapa_registerFile.get_estado()}\n"
        estado += f"  Execute:      {self.etapa_execute.get_estado()}\n"
        estado += f"  Store:        {self.etapa_store.get_estado()}\n"
        return estado

    def tick(self):
        """
        Simula un ciclo de reloj discreto del pipeline.
        - Primero, las etapas reducen sus ciclos internos (tick)
        - Luego, movemos instrucciones entre etapas si ambas condiciones se cumplen:
          1. Etapa actual completó (ciclos_restantes == 0 después de tick)
          2. Etapa siguiente está libre
        """
        # 1. Tick en todas las etapas (reduce ciclos restantes)
        self.etapa_fetch.tick()
        self.etapa_decode.tick()
        self.etapa_registerFile.tick()
        self.etapa_execute.tick()
        self.etapa_store.tick()

        # 2. Mover instrucciones entre etapas (de Store hacia Fetch en ese orden)
        #    Esto simula que al final de cada ciclo, si una etapa termina, 
        #    pasa su instrucción a la siguiente (si está libre)

        # Store → Writeback (si completa, ejecutar efecto: mem/reg write)
        if self.etapa_store.getInstruccion() != "":
            instr_store = self.etapa_store.get_instruccion_actual()
            self.log(f"[CICLO {self.ciclo_actual}] [COMPLETADA] {instr_store}")
            # Ejecutar efectos pasados en params (si existen)
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
                        # escribir en memoria de datos
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
                        # Branch evaluation result
                        branch_taken, label_or_offset = params[1], params[2]
                        if branch_taken:
                            # Resolver label o usar offset directo
                            if label_or_offset in self.labels:
                                nuevo_pc = self.labels[label_or_offset]
                            else:
                                # Asumir offset relativo (en bytes, múltiplo de 4)
                                try:
                                    nuevo_pc = self.indice_instruccion + int(label_or_offset) * 4
                                except:
                                    nuevo_pc = self.indice_instruccion
                            
                            self.log(f"[STORE] Branch TOMADO: PC = {self.indice_instruccion} -> {nuevo_pc}")
                            self.indice_instruccion = nuevo_pc
                            
                            # Flush pipeline (limpiar Fetch, Decode, RegisterFile, Execute)
                            self.etapa_fetch.instruccionEjecutando = ""
                            self.etapa_fetch.ocupada = False
                            self.etapa_decode.instruccionEjecutando = ""
                            self.etapa_decode.ocupada = False
                            self.etapa_registerFile.instruccionEjecutando = ""
                            self.etapa_registerFile.ocupada = False
                            self.etapa_execute.instruccionEjecutando = ""
                            self.etapa_execute.ocupada = False
                            self.log(f"[STORE] Pipeline flushed (Fetch/Decode/RegFile/Execute)")
                        else:
                            self.log(f"[STORE] Branch NO tomado")
                    elif accion == 'jump_result':
                        # Jump (jal) - siempre se toma
                        rd, label = params[1], params[2]
                        
                        # Buscar el PC de la instrucción jal actual
                        # La instrucción está en etapa_store, necesitamos encontrar su índice original
                        instr_actual = self.etapa_store.get_instruccion_actual()
                        pc_jal = -1
                        for i, instr in enumerate(self.codigo):
                            if instr == instr_actual:
                                pc_jal = i * 4  # PC en múltiplos de 4
                                break
                        
                        # Guardar dirección de retorno (PC de jal + 4) en rd
                        if 0 < rd < len(self.regs) and pc_jal >= 0:  # x0 no puede ser escrito
                            return_addr = pc_jal + 4
                            self.regs[rd] = return_addr
                            self.log(f"[STORE] JAL: x{rd} <- {return_addr} (return address)")
                        
                        # Resolver label y actualizar PC
                        if label in self.labels:
                            nuevo_pc = self.labels[label]
                        else:
                            # Asumir offset relativo desde PC de jal (en bytes)
                            try:
                                nuevo_pc = pc_jal + int(label) * 4
                            except:
                                nuevo_pc = pc_jal + 4
                        
                        self.log(f"[STORE] JAL: PC = {pc_jal} -> {nuevo_pc}")
                        self.indice_instruccion = nuevo_pc
                        
                        # Flush pipeline (limpiar Fetch, Decode, RegisterFile, Execute)
                        self.etapa_fetch.instruccionEjecutando = ""
                        self.etapa_fetch.ocupada = False
                        self.etapa_decode.instruccionEjecutando = ""
                        self.etapa_decode.ocupada = False
                        self.etapa_registerFile.instruccionEjecutando = ""
                        self.etapa_registerFile.ocupada = False
                        self.etapa_execute.instruccionEjecutando = ""
                        self.etapa_execute.ocupada = False
                        self.log(f"[STORE] Pipeline flushed (Fetch/Decode/RegFile/Execute)")
            except Exception:
                pass
            # Limpiar la etapa Store después de completar
            self.etapa_store.instruccionEjecutando = ""
            self.etapa_store.ocupada = False

        # Execute → Store (si Execute completa y Store está libre)
        if self.etapa_execute.getInstruccion() != "" and self.etapa_store.esta_libre():
            instr = self.etapa_execute.getInstruccion()
            # Obtener params que Execute.py ya calculó
            params = getattr(self.etapa_execute, 'params', []) or []
            
            self.etapa_store.cargarInstruccion(instr, params)
            # Limpiar Execute
            self.etapa_execute.instruccionEjecutando = ""
            self.etapa_execute.ocupada = False

        # RegisterFile → Execute (si RegFile completa y Execute está libre)
        if self.etapa_registerFile.getInstruccion() != "" and self.etapa_execute.esta_libre():
            instr = self.etapa_registerFile.getInstruccion()
            # Pasar los params (operandos leídos) que RegisterFile calculó
            params = getattr(self.etapa_registerFile, 'params', []) or []
            self.etapa_execute.cargarInstruccion(instr, params)
            # Limpiar RegisterFile
            self.etapa_registerFile.instruccionEjecutando = ""
            self.etapa_registerFile.ocupada = False

        # Decode → RegisterFile (si Decode completa y RegFile está libre)
        if self.etapa_decode.getInstruccion() != "" and self.etapa_registerFile.esta_libre():
            instr = self.etapa_decode.getInstruccion()
            self.etapa_registerFile.cargarInstruccion(instr)
            # Limpiar Decode
            self.etapa_decode.instruccionEjecutando = ""
            self.etapa_decode.ocupada = False

        # Fetch → Decode (si Fetch completa y Decode está libre)
        if self.etapa_fetch.getInstruccion() != "" and self.etapa_decode.esta_libre():
            instr = self.etapa_fetch.getInstruccion()
            self.etapa_decode.cargarInstruccion(instr, [])
            # Limpiar Fetch
            self.etapa_fetch.instruccionEjecutando = ""
            self.etapa_fetch.ocupada = False

        # 3. Cargar siguiente instrucción en Fetch (si hay y Fetch está libre)
        if self.indice_instruccion < len(self.instrucciones_cola) * 4 and self.etapa_fetch.esta_libre():
            instr = self.instrucciones_cola[self.indice_instruccion // 4]
            self.etapa_fetch.cargarInstruccion(instr, [])
            self.indice_instruccion += 4

        self.ciclo_actual += 1

    def ejecutar(self):
        """Ejecuta el programa completo en ciclos de reloj discretos."""
        self.log("\n=== INICIANDO SIMULACIÓN DEL PIPELINE CON CONTROL DE HAZARDS ===\n")
        
        # Simulación de ciclos de reloj
        ciclos_max = 1000  # Prevención de bucle infinito
        
        #CICLO PRINCIPAL
        while self.ciclo_actual < ciclos_max:
            # Mostrar estado antes del tick
            self.log(self.mostrar_estado_pipeline())
            
            # Ejecutar un ciclo
            self.tick()
            
            # Condición de salida: no hay más instrucciones y pipeline está vacío
            if (self.indice_instruccion >= len(self.instrucciones_cola) * 4 and
                self.etapa_fetch.get_instruccion_actual() == "" and
                self.etapa_decode.get_instruccion_actual() == "" and
                self.etapa_registerFile.get_instruccion_actual() == "" and
                self.etapa_execute.get_instruccion_actual() == "" and
                self.etapa_store.get_instruccion_actual() == ""):
                break
        
        self.log("\n" + "=" * 80)
        self.log(f"[SIMULACIÓN COMPLETADA] Total de ciclos: {self.ciclo_actual}")
        self.log("=" * 80 + "\n")
        # Guardar memoria de datos en archivo (mismo comportamiento que CPU)
        try:
            self.guardar_memoria_en_archivo("memoria_salida_hazard_control.txt")
        except Exception:
            pass
        self.log_file.close()

    def guardar_memoria_en_archivo(self, ruta):
        """Guarda el contenido de la memoria de datos en un archivo."""
        # Guardar en el directorio Front para que el frontend lo encuentre
        mem_dir = Path(__file__).parent.parent / "Front"
        mem_path = mem_dir / ruta
        with open(mem_path, "w", encoding="utf-8") as f:
            for i, valor in enumerate(self.mem_data.data):
                f.write(f"[{i:03d}] -> {valor}\n")
        self.log(f"Estado de memoria escrito en {ruta}")