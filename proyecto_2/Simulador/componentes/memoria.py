class Memoria:
    def __init__(self, size):
        self.data: list[int | str] = [0] * size  # puede almacenar ints o strings (instrucciones)

    def escribir(self, direccion, valor):
        """Guarda un valor en una dirección de memoria."""
        if 0 <= direccion < len(self.data):
            self.data[direccion] = valor
        else:
            raise IndexError("Dirección de memoria fuera de rango")

    def leer(self, direccion):
        """Lee un valor de una dirección de memoria."""
        if 0 <= direccion < len(self.data):
            return self.data[direccion]
        else:
            raise IndexError("Dirección de memoria fuera de rango")

    def mostrar(self, inicio=0, fin=16):
        """Muestra un rango de direcciones de memoria."""
        print("=== MEMORIA ===")
        for i in range(inicio, min(fin, len(self.data))):
            print(f"[{i:03d}] -> {self.data[i]}")
        print("================")