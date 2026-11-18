from machine import Pin

class SensorLDR:
    def __init__(self, pino=18):
        self.pino = Pin(pino, Pin.IN)

    def ler(self):
        luz = self.pino.value()
        return {"luz": luz, "estado": "Claro" if luz == 0 else "Escuro"}
