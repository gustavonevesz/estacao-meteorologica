import time
import ujson
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
        print("\n[CICLO] Iniciando leitura dos sensores")
        dados = {"estacao_id": config.ESTACAO_ID}
        for sensor in sensores:
            # Um driver com defeito nao pode parar o envio dos demais sensores.
            try:
                leitura = sensor.ler()
                dados.update(leitura)
                print("[SENSOR]", sensor.__class__.__name__, ujson.dumps(leitura))
            except Exception as erro:
                print("Falha inesperada em", sensor.__class__.__name__, ":", erro)
        # Mostra JSON de verdade: null/true/false, como no corpo enviado a API.
        # Senha Wi-Fi e API_KEY pertencem aos cabecalhos/configuracao, nao ao payload.
        print("[PAYLOAD JSON]", ujson.dumps(dados))
        try:
            print("[WIFI] Verificando conexao")
            wifi = conectar(config.WIFI_SSID, config.WIFI_PASSWORD)
            print("[WIFI] Conectado | IP:", wifi.ifconfig()[0])
            print("[HTTP] Enviando POST com JSON para a API")
            enviar(config.API_URL, config.API_KEY, dados)
            # enviar() so retorna normalmente quando o servidor respondeu 201.
            print("[HTTP] 201 Created | leitura salva na API")
        except (OSError, ValueError) as erro:
            print("Falha no envio; nova tentativa no proximo ciclo:", erro)
        time.sleep(max(3, config.INTERVALO_SEGUNDOS))


main()
