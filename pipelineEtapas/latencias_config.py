# Configuración de latencias por etapa (en ciclos de reloj)
# Basadas en procesadores reales RISC-V, ARM y x86

LATENCIES_CONFIG = {
    # Fetch: 1 ciclo
    # - Acceso a memoria de instrucciones (L1 instruction cache hit)
    # - Muy rápido si está en caché
    'Fetch': 1,
    
    # Decode: 1 ciclo
    # - Decodificación de instrucción
    # - Lectura del archivo de registros
    # - Muy parallelizable en CPUs modernas
    'Decode': 1,
    
    # RegisterFile: 1 ciclo
    # - Lectura de registros
    # - Típicamente junto a decode, pero separado en análisis
    'RegisterFile': 1,
    
    # Execute: 2-3 ciclos (variable según instrucción)
    # - Suma/resta: 1 ciclo
    # - Multiplicación: 3-5 ciclos
    # - Promedio: 2 ciclos
    # Para simplificar, usamos 2 como base (puede variar por instrucción)
    'Execute': 2,
    
    # Store: 1 ciclo
    # - Writeback a registros
    # - Acceso a L1 data cache (si es write)
    'Store': 1,
}

# Estado of the art: procesadores modernos (2024)
# - AMD Ryzen 9 9950X: latencia L/S ≈ 4-5 ciclos (3 ciclos L1 caché)
# - Intel Core Ultra: latencia L/S ≈ 4-5 ciclos
# - Nuestro modelo simplificado: latencia total ≈ 1+1+1+2+1 = 6 ciclos (sin hazards)

INSTRUCTION_LATENCIES = {
    # Instrucciones y sus latencias específicas (si se requiere precisión)
    'add': 1,      # ALU integer
    'addi': 1,
    'sub': 1,
    'mul': 3,      # Multiplicación
    'div': 10,     # División (muy lenta)
    'lw': 4,       # Load (3-4 ciclos por cache miss)
    'sw': 1,       # Store
    'blt': 1,      # Branch (predice en Fetch/Decode)
    'beq': 1,
    'jal': 1,
    'nop': 1,      # No operation
}

def get_stage_latency(stage_name):
    """Retorna la latencia en ciclos para una etapa."""
    return LATENCIES_CONFIG.get(stage_name, 1)

def get_instruction_latency(opcode):
    """Retorna la latencia específica para una instrucción."""
    return INSTRUCTION_LATENCIES.get(opcode, 1)