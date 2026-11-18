import time
import config
from wifi import conectar
from api_client import enviar
from sensors.ldr import SensorLDR
from sensors.dht22 import SensorDHT22
from sensors.mq135 import SensorMQ135
from sensors.bmp280 import SensorBMP280


def main():
    sensores = [
        SensorLDR(pino=18),
        SensorDHT22(pino=4),
        SensorMQ135(pino=34),
        SensorBMP280(scl=22, sda=21),
    ]
    while True:
        dados = {"estacao_id": config.ESTACAO_ID}
        for sensor in sensores:
            # Um driver com defeito nao pode parar o envio dos demais sensores.
            try:
                dados.update(sensor.ler())
            except Exception as erro:
                print("Falha inesperada em", sensor.__class__.__name__, ":", erro)
        print(dados)
        try:
            conectar(config.WIFI_SSID, config.WIFI_PASSWORD)
            enviar(config.API_URL, config.API_KEY, dados)
            print("Leitura salva na API")
        except (OSError, ValueError) as erro:
            print("Falha no envio; nova tentativa no proximo ciclo:", erro)
        time.sleep(max(3, config.INTERVALO_SEGUNDOS))


main()
