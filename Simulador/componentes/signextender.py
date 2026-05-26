class SignExtender:
    @staticmethod
    def extender(valor, bits_origen=12, bits_destino=32):
        """
        Extiende el signo de un número (como los inmediatos de RISC-V).
        Ejemplo: extender(0b111111111111, 12) → -1
        """
        mask = 1 << (bits_origen - 1)
        if valor & mask:
            valor = valor - (1 << bits_origen)
        return valor