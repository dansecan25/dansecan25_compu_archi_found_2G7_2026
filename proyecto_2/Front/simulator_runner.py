"""
Módulo para ejecutar simulaciones del CPU desde el frontend.
Conecta el frontend con el backend del simulador.
Soporta 4 tipos de procesadores según el proyecto:
a) Procesador uniciclo
b) Procesador multiciclo
c) Procesador segmentado con riesgos y solucionando con stalls
d) Procesador segmentado con unidad de riesgos y adelantamiento
"""
import sys
import os
from pathlib import Path

# Agregar el directorio padre al path para importar módulos del Simulador
sys.path.insert(0, str(Path(__file__).parent.parent))

from Simulador.cpuUniciclo import CPUUniciclo
from Simulador.cpuMulticiclo import CPUMulticiclo
from Simulador.cpuPipelineSinHazards import CPUpipelineNoHazard
from Simulador.cpuPipelineHazardControl import CPUPipelineHazardControl
from Simulador.cpuPipelineConPredicciondeSaltos import CPUpipelineConPrediccionSaltos
from Simulador.cpuPipelinePrediccionSaltosHazardControl import CPUPipelinePrediccionSaltosHazardControl


class SimulatorRunner:
    """
    Clase para ejecutar simulaciones de CPU y generar archivos de log.
    Soporta 6 tipos de procesadores:
    0: Uniciclo
    1: Multiciclo
    2: Pipeline sin Hazards
    3: Pipeline con Hazard Control
    4: Pipeline con Predicción de Saltos
    5: Pipeline con Predicción + Hazard Control
    """
    
    # Mapeo de índices a clases de CPU
    CPU_CLASSES = {
        0: CPUUniciclo,
        1: CPUMulticiclo,
        2: CPUpipelineNoHazard,
        3: CPUPipelineHazardControl,
        4: CPUpipelineConPrediccionSaltos,
        5: CPUPipelinePrediccionSaltosHazardControl
    }
    
    # Nombres de archivos de log por CPU
    LOG_FILES = {
        0: "log_uniciclo.txt",
        1: "log_multiciclo.txt",
        2: "log.txt",
        3: "log_hazard_control.txt",
        4: "log_prediccion.txt",
        5: "log_prediccion_hazard_control.txt"
    }
    
    # Nombres de archivos de memoria por CPU
    MEMORY_FILES = {
        0: "memoria_salida_uniciclo.txt",
        1: "memoria_salida_multiciclo.txt",
        2: "memoria_salida.txt",
        3: "memoria_salida_hazard_control.txt",
        4: "memoria_salida_prediccion.txt",
        5: "memoria_salida_prediccion_hazard_control.txt"
    }
    
    # Nombres descriptivos de las CPUs
    CPU_NAMES = {
        0: "CPU Uniciclo",
        1: "CPU Multiciclo",
        2: "CPU Pipeline sin Hazards",
        3: "CPU Pipeline con Hazard Control",
        4: "CPU Pipeline con Predicción de Saltos",
        5: "CPU Pipeline con Predicción + Hazard Control"
    }
    
    @staticmethod
    def run_simulation(cpu_index: int, code: list[str], predictor_strategy: str = 'always_taken') -> bool:
        """
        Ejecuta una simulación con la CPU especificada.
        
        Args:
            cpu_index: Índice de la CPU (0-5)
            code: Lista de líneas de código RISC-V
            predictor_strategy: Estrategia de predicción ('always_taken' o 'always_not_taken')
        
        Returns:
            True si la simulación fue exitosa, False en caso contrario
        """
        try:
            print(f"\n{'='*80}")
            print(f"Ejecutando simulación: {SimulatorRunner.CPU_NAMES[cpu_index]}")
            print(f"{'='*80}")
            
            # Crear instancia de la CPU correspondiente
            if cpu_index in [4, 5]:  # CPUs con predicción de saltos
                cpu = SimulatorRunner.CPU_CLASSES[cpu_index](predictor_strategy=predictor_strategy)
            else:
                cpu = SimulatorRunner.CPU_CLASSES[cpu_index]()
            
            # Cargar y ejecutar el código
            cpu.cargarCodigo(code)
            cpu.ejecutar()
            
            print(f"\n[OK] Simulacion completada exitosamente")
            print(f"  - Log generado: {SimulatorRunner.LOG_FILES[cpu_index]}")
            print(f"  - Memoria guardada: {SimulatorRunner.MEMORY_FILES[cpu_index]}")
            
            return True
            
        except Exception as e:
            print(f"\n[ERROR] Error en simulacion {SimulatorRunner.CPU_NAMES[cpu_index]}: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    @staticmethod
    def run_dual_simulation(cpu_pair_index: int, code: list[str]) -> tuple[bool, bool]:
        """
        Ejecuta dos simulaciones según el par seleccionado.
        
        Args:
            cpu_pair_index: Índice del par de CPUs
                0: Uniciclo (0) y Multiciclo (1)
                1: Pipeline sin Hazards (2) y Pipeline con Hazard Control (3)
                2: Pipeline con Predicción (4) y Pipeline con Predicción + Hazard (5)
            code: Lista de líneas de código RISC-V
        
        Returns:
            Tupla (success_cpu1, success_cpu2)
        """
        if cpu_pair_index == 0:
            # Par 1: Uniciclo y Multiciclo
            cpu1_index = 0
            cpu2_index = 1
        elif cpu_pair_index == 1:
            # Par 2: Pipeline sin Hazards y Pipeline con Hazard Control
            cpu1_index = 2
            cpu2_index = 3
        else:
            # Par 3: Pipeline con Predicción y Pipeline con Predicción + Hazard
            cpu1_index = 4
            cpu2_index = 5
        
        print(f"\n{'#'*80}")
        print(f"# EJECUTANDO PAR DE SIMULACIONES")
        print(f"# CPU 1: {SimulatorRunner.CPU_NAMES[cpu1_index]}")
        print(f"# CPU 2: {SimulatorRunner.CPU_NAMES[cpu2_index]}")
        print(f"{'#'*80}\n")
        
        # Ejecutar primera simulación
        success1 = SimulatorRunner.run_simulation(cpu1_index, code)
        
        # Ejecutar segunda simulación
        success2 = SimulatorRunner.run_simulation(cpu2_index, code)
        
        print(f"\n{'#'*80}")
        print(f"# RESUMEN DE SIMULACIONES")
        print(f"# {SimulatorRunner.CPU_NAMES[cpu1_index]}: {'[OK]' if success1 else '[ERROR]'}")
        print(f"# {SimulatorRunner.CPU_NAMES[cpu2_index]}: {'[OK]' if success2 else '[ERROR]'}")
        print(f"{'#'*80}\n")
        
        return success1, success2


# Función de prueba
if __name__ == "__main__":
    # Código de prueba simple
    test_code = [
        "# TEST SIMPLE",
        "addi x1, x0, 10",
        "addi x2, x0, 20",
        "add x3, x1, x2",
        "addi x10, x0, 0",
        "sw x1, 0(x10)",
        "sw x2, 4(x10)",
        "sw x3, 8(x10)",
        "lw x4, 0(x10)",
        "beq x1, x2, skip1",
        "addi x5, x0, 50",
        "skip1:",
        "beq x1, x1, skip2",
        "addi x6, x0, 99",
        "skip2:",
        "addi x7, x0, 77",
        "nop"
    ]
    
    # Ejecutar par de simulaciones
    SimulatorRunner.run_dual_simulation(0, test_code)

# Made with Bob
