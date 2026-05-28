class MUX:
    @staticmethod
    def seleccionar(a, b, sel):
        """
        Si sel = 0, devuelve a.
        Si sel = 1, devuelve b.
        """
        return b if sel else a