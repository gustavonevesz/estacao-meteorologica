from machine import Pin, ADC

class SensorMQ135:
    def __init__(self, pino=34):
        self.sensor = ADC(Pin(pino))
        self.sensor.atten(ADC.ATTN_11DB)
        self.sensor.width(ADC.WIDTH_12BIT)

    def ler(self):
        try:
            return {"gas": self.sensor.read()}
        except OSError as erro:
            print("MQ-135:", erro)
            return {"gas": None}
