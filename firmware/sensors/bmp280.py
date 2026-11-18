from machine import Pin, SoftI2C
import struct
import time

class BMP280:

    def __init__(self, i2c, endereco):

        self.i2c = i2c
        self.endereco = endereco

        # Reinicia e espera a copia dos coeficientes de fabrica.
        i2c.writeto_mem(endereco, 0xE0, bytes([0xB6]))
        time.sleep_ms(10)
        self._aguardar(0x01)

        # Le os coeficientes de calibracao
        dados = i2c.readfrom_mem(
            endereco, 0x88, 24
        )

        self.cal = struct.unpack(
            "<HhhHhhhhhhhh", dados
        )

        if dados == bytes(24) or dados == bytes([255]) * 24 or not self.cal[0] or not self.cal[3]:
            raise ValueError("Coeficientes de fabrica invalidos")

        # Configura o sensor
        i2c.writeto_mem(
            endereco, 0xF5, bytes([0])
        )

        i2c.writeto_mem(
            endereco, 0xF4, bytes([0x54])
        )

    def _aguardar(self, mascara, timeout_ms=1000, aguardar_sleep=False):
        inicio = time.ticks_ms()
        while True:
            ocupado = self.i2c.readfrom_mem(self.endereco, 0xF3, 1)[0] & mascara
            modo = self.i2c.readfrom_mem(self.endereco, 0xF4, 1)[0] & 3 if aguardar_sleep else 0
            if not ocupado and not modo:
                return
            if time.ticks_diff(time.ticks_ms(), inicio) >= timeout_ms:
                raise OSError("BMP280: timeout durante inicializacao ou medicao")
            time.sleep_ms(2)

    def ler(self):

        # Temperatura x2, pressao x16, modo forcado; nao depende do navegador.
        self.i2c.writeto_mem(self.endereco, 0xF4, bytes([0x55]))
        time.sleep_ms(2)
        self._aguardar(0x09, aguardar_sleep=True)

        dados = self.i2c.readfrom_mem(
            self.endereco, 0xF7, 6
        )

        adc_p = (
            (dados[0] << 12)
            | (dados[1] << 4)
            | (dados[2] >> 4)
        )

        adc_t = (
            (dados[3] << 12)
            | (dados[4] << 4)
            | (dados[5] >> 4)
        )

        # Zero nao significa 0 graus Celsius. Nao publicar compensacao invalida.
        if adc_t in (0, 0x80000, 0xFFFFF):
            raise ValueError("Temperatura bruta invalida: " + hex(adc_t))
        if adc_p in (0, 0x80000, 0xFFFFF):
            raise ValueError("Pressao bruta invalida: " + hex(adc_p))

        (
            t1, t2, t3,
            p1, p2, p3, p4, p5,
            p6, p7, p8, p9
        ) = self.cal

        # TEMPERATURA
        var1 = (
            (adc_t / 16384.0 - t1 / 1024.0)
            * t2
        )

        var2 = (
            (adc_t / 131072.0 - t1 / 8192.0) ** 2
        ) * t3

        t_fine = var1 + var2

        temperatura_bmp = t_fine / 5120.0

        # PRESSAO ATMOSFERICA
        var1 = t_fine / 2.0 - 64000.0

        var2 = var1 * var1 * p6 / 32768.0
        var2 = var2 + var1 * p5 * 2.0
        var2 = var2 / 4.0 + p4 * 65536.0

        var1 = (
            p3 * var1 * var1 / 524288.0
            + p2 * var1
        ) / 524288.0

        var1 = (1.0 + var1 / 32768.0) * p1

        if var1 == 0:
            raise ValueError(
                "Calibracao de pressao invalida"
            )

        pressao = 1048576.0 - adc_p

        pressao = (
            (pressao - var2 / 4096.0)
            * 6250.0 / var1
        )

        var1 = (
            p9 * pressao * pressao
            / 2147483648.0
        )

        var2 = pressao * p8 / 32768.0

        pressao = (
            pressao + (var1 + var2 + p7) / 16.0
        )

        pressao_hpa = pressao / 100.0

        if not (-40 <= temperatura_bmp <= 85 and 300 <= pressao_hpa <= 1100):
            raise ValueError("Medicao BMP280 fora da faixa; verificar sensor e montagem")

        return (
            round(temperatura_bmp, 1),
            round(pressao_hpa, 2)
        )

class SensorBMP280:
    def __init__(self, scl=22, sda=21):
        self.i2c = SoftI2C(scl=Pin(scl), sda=Pin(sda), freq=50000, timeout=5000)
        self.sensor = None
        self.ultima_busca = None

    def ler(self):
        agora = time.ticks_ms()
        if self.sensor is None and (self.ultima_busca is None or time.ticks_diff(agora, self.ultima_busca) >= 5000):
            self.ultima_busca = agora
            for endereco in (0x76, 0x77):
                try:
                    identificador = self.i2c.readfrom_mem(endereco, 0xD0, 1)[0]
                except OSError:
                    continue
                if identificador != 0x58:
                    print("BMP280: ID diferente em", hex(endereco), hex(identificador))
                    continue
                try:
                    self.sensor = BMP280(self.i2c, endereco)
                    break
                except (OSError, ValueError) as erro:
                    print("BMP280 detectado, mas falhou ao iniciar:", erro)
        if self.sensor is not None:
            try:
                temperatura, pressao = self.sensor.ler()
                return {"temperatura_bmp": temperatura, "pressao": pressao, "bmp_conectado": True}
            except (OSError, ValueError, ZeroDivisionError) as erro:
                print("BMP280:", erro)
                self.sensor = None
                self.ultima_busca = agora
        return {"temperatura_bmp": None, "pressao": None, "bmp_conectado": False}
