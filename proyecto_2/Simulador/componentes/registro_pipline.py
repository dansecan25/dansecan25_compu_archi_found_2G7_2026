class RegistroPipeline:
    """
    Simula los registros entre etapas del pipeline (IF/ID, ID/EX, EX/MEM, MEM/WB).
    Guarda las señales y valores que pasan de una etapa a la siguiente.
    """
    def __init__(self):
        self.data = {}

    def escribir(self, key, valor):
        self.data[key] = valor

    def leer(self, key):
        return self.data.get(key, None)

    def limpiar(self):
        self.data = {}

    def mostrar(self):
        print("=== REGISTRO PIPELINE ===")
        for k, v in self.data.items():
            print(f"{k}: {v}")
        print("=========================")