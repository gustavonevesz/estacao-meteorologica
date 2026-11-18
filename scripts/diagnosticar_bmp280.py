"""Executar no ESP32 via mpremote run; mantem a montagem atual SDA21/SCL22.

O programa normal fica pausado durante o teste. Reinicie a placa depois.
Nao importa main/config nem aplica temperatura externa ou correcao artificial.
"""
from machine import I2C, Pin, SoftI2C
import struct
import time


def diagnosticar():
    controlador = I2C(0, scl=Pin(22), sda=Pin(21), freq=100000)
    controlador.deinit()
    sda = Pin(21, Pin.IN)
    scl = Pin(22, Pin.IN)
    time.sleep_ms(200)
    print("LINHAS SDA21 SCL22:", sda.value(), scl.value())
    if not (sda.value() and scl.value()):
        print("Uma linha esta baixa. Isso nao prova curto; conferir montagem e alimentacao.")
        return
    i2c = SoftI2C(scl=Pin(22), sda=Pin(21), freq=50000, timeout=5000)
    encontrados = i2c.scan()
    print("ENDERECOS:", [hex(a) for a in encontrados])
    endereco = next((a for a in (0x76, 0x77) if a in encontrados), None)
    if endereco is None:
        print("BMP280 nao localizado nos enderecos esperados.")
        return
    identificador = i2c.readfrom_mem(endereco, 0xD0, 1)[0]
    print("ID:", hex(identificador))
    if identificador != 0x58:
        print("Este teste espera um BMP280 ID 0x58.")
        return
    i2c.writeto_mem(endereco, 0xE0, bytes([0xB6]))
    time.sleep_ms(100)
    if i2c.readfrom_mem(endereco, 0xF3, 1)[0] & 1:
        print("Calibracao ainda ocupada apos reset; teste interrompido.")
        return
    calibracao = struct.unpack("<HhhHhhhhhhhh", i2c.readfrom_mem(endereco, 0x88, 24))
    print("COEFICIENTES:", calibracao)
    # Perfil normal usado pela biblioteca Adafruit: T x16, P x16, filtro desligado.
    i2c.writeto_mem(endereco, 0xF5, bytes([0]))
    i2c.writeto_mem(endereco, 0xF4, bytes([0xB7]))
    for numero in range(6):
        time.sleep_ms(2000)
        bruto = i2c.readfrom_mem(endereco, 0xF7, 6)
        separada = bytearray([0xAA, 0xAA, 0xAA])
        i2c.readfrom_mem_into(endereco, 0xFA, separada)
        i2c.writeto(endereco, bytes([0xFA]), True)
        com_stop = i2c.readfrom(endereco, 3)
        print("SEGUNDOS", (numero + 1) * 2, "RAW6", bruto.hex(),
              "TEMP3", separada.hex(), "TEMP_STOP", com_stop.hex())
    adc_t = (bruto[3] << 12) | (bruto[4] << 4) | (bruto[5] >> 4)
    if adc_t in (0, 0x80000, 0xFFFFF):
        print("VEREDITO: temperatura bruta invalida. Nao publicar pressao compensada.")
    else:
        from sensors.bmp280 import BMP280
        try:
            print("MEDICAO VALIDADA (C, hPa):", BMP280(i2c, endereco).ler())
        except (OSError, ValueError, ZeroDivisionError) as erro:
            print("Falha na validacao:", erro)


try:
    diagnosticar()
except Exception as erro:
    print("ERRO NO DIAGNOSTICO:", repr(erro))
finally:
    Pin(21, Pin.IN, Pin.PULL_UP)
    Pin(22, Pin.IN, Pin.PULL_UP)
    print("Teste encerrado. Reinicie o ESP32 para retomar as coletas.")
