class ALU:
    def __init__(self):
        self.resultado = 0
        self.zero = 0  # bandera para instrucciones tipo BEQ

    def operar(self, operacion, a, b):
        """Ejecuta una operación aritmética/lógica."""
        if operacion == "add":
            self.resultado = a + b
        elif operacion == "sub":
            self.resultado = a - b
        elif operacion == "and":
            self.resultado = a & b
        elif operacion == "or":
            self.resultado = a | b
        elif operacion == "xor":
            self.resultado = a ^ b
        elif operacion == "slt":
            self.resultado = 1 if a < b else 0
        else:
            raise ValueError(f"Operación ALU no soportada: {operacion}")

        # Bandera de zero 
        self.zero = 1 if self.resultado == 0 else 0
        return self.resultado