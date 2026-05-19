class BancoRegistros:
    def __init__(self):
        # 32 registros inicializados en 0
        self.reg = [0] * 32

    def leer(self, idx):
        """Devuelve el valor del registro idx."""
        return self.reg[idx]

    def escribir(self, idx, valor):
        """Escribe valor en el registro idx (excepto x0)."""
        if idx != 0:
            self.reg[idx] = valor

    def mostrar(self):
        """Imprime todos los registros."""
        print("=== REGISTROS ===")
        for i in range(32):
            print(f"x{i:02d}: {self.reg[i]}")
        print("=================")