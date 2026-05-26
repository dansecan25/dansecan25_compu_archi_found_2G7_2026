"""
Módulo para ejecutar simulaciones del CPU desde el frontend.
Conecta el frontend con el backend del simulador.
"""
import sys
import os
from pathlib import Path

# Agregar el directorio padre al path para importar módulos del Simulador
sys.path.insert(0, str(Path(__file__).parent.parent))

from Simulador.cpuPipelineSinHazards import CPUpipelineNoHazard
from Simulador.cpuPipelineHazardControl import CPUPipelineHazardControl
from Simulador.cpuPipelineConPredicciondeSaltos import CPUpipelineConPrediccionSaltos
from Simulador.cpuPipelinePrediccionSaltosHazardControl import CPUPipelinePrediccionSaltosHazardControl


class SimulatorRunner:
    """
    Clase para ejecutar simulaciones de CPU y generar archivos de log.
    """
    
    # Mapeo de índices a clases de CPU
    CPU_CLASSES = {
        0: CPUpipelineNoHazard,
        1: CPUpipelineConPrediccionSaltos,
        2: CPUPipelineHazardControl,
        3: CPUPipelinePrediccionSaltosHazardControl
    }
    
    # Nombres de archivos de log por CPU
    LOG_FILES = {
        0: "log.txt",
        1: "log_prediccion.txt",
        2: "log_hazard_control.txt",
        3: "log_prediccion_hazard_control.txt"
    }
    
    # Nombres de archivos de memoria por CPU
    MEMORY_FILES = {
        0: "memoria_salida.txt",
        1: "memoria_salida_prediccion.txt",
        2: "memoria_salida_hazard_control.txt",
        3: "memoria_salida_prediccion_hazard_control.txt"
    }
    
    # Nombres descriptivos de las CPUs
    CPU_NAMES = {
        0: "CPU sin Hazards",
        1: "CPU con Predicción de Saltos",
        2: "CPU con Hazard Control",
        3: "CPU con Predicción de Saltos y Hazard Control"
    }
    
    @staticmethod
    def run_simulation(cpu_index: int, code: list[str], predictor_strategy: str = 'always_taken') -> bool:
        """
        Ejecuta una simulación con la CPU especificada.
        
        Args:
            cpu_index: Índice de la CPU (0-3)
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
            if cpu_index in [1, 3]:  # CPUs con predicción de saltos
                cpu = SimulatorRunner.CPU_CLASSES[cpu_index](predictor_strategy=predictor_strategy)
            else:
                cpu = SimulatorRunner.CPU_CLASSES[cpu_index]()
            
            # Cargar y ejecutar el código
            cpu.cargarCodigo(code)
            cpu.ejecutar()
            
            print(f"\n✓ Simulación completada exitosamente")
            print(f"  - Log generado: {SimulatorRunner.LOG_FILES[cpu_index]}")
            print(f"  - Memoria guardada: {SimulatorRunner.MEMORY_FILES[cpu_index]}")
            
            return True
            
        except Exception as e:
            print(f"\n✗ Error en simulación {SimulatorRunner.CPU_NAMES[cpu_index]}: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    @staticmethod
    def run_dual_simulation(cpu_pair_index: int, code: list[str]) -> tuple[bool, bool]:
        """
        Ejecuta dos simulaciones según el par seleccionado.
        
        Args:
            cpu_pair_index: Índice del par de CPUs
                0: CPU_NH (0) y CPU_HC (2)
                1: CPU_PS (1) y CPU_PS+HC (3)
            code: Lista de líneas de código RISC-V
        
        Returns:
            Tupla (success_cpu1, success_cpu2)
        """
        if cpu_pair_index == 0:
            # Par 1: CPU sin Hazards (0) y CPU con Hazard Control (2)
            cpu1_index = 0
            cpu2_index = 2
        else:
            # Par 2: CPU con Predicción (1) y CPU con Predicción + Hazard (3)
            cpu1_index = 1
            cpu2_index = 3
        
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
        print(f"# {SimulatorRunner.CPU_NAMES[cpu1_index]}: {'✓ OK' if success1 else '✗ ERROR'}")
        print(f"# {SimulatorRunner.CPU_NAMES[cpu2_index]}: {'✓ OK' if success2 else '✗ ERROR'}")
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
