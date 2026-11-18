from machine import Pin
import dht
import time

class SensorDHT22:
    def __init__(self, pino=4):
        self.sensor = dht.DHT22(Pin(pino))
        self.ultima = None
        self.dados = {"temperatura": None, "umidade": None}

    def ler(self):
        agora = time.ticks_ms()
        if self.ultima is None or time.ticks_diff(agora, self.ultima) >= 2500:
            self.ultima = agora
            try:
                self.sensor.measure()
                self.dados = {"temperatura": round(self.sensor.temperature(), 1), "umidade": round(self.sensor.humidity(), 1)}
            except OSError as erro:
                print("DHT22:", erro)
                self.dados = {"temperatura": None, "umidade": None}
        return self.dados
