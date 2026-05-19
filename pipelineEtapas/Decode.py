

from .latencias_config import get_stage_latency

class Decode():
    def __init__(self):
        self.instruccionEjecutando = ""
        self.params = []
        self.ciclos_restantes = 0
        self.ocupada = False
        self.latencia = get_stage_latency('Decode')

    def cargarInstruccion(self, instruccion, params):
        """Carga una instrucción si la etapa está libre."""
        if not self.ocupada:
            self.instruccionEjecutando = instruccion
            self.params = params
            self.ciclos_restantes = self.latencia
            self.ocupada = True
            
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