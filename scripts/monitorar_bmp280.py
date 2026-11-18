"""Monitor de 90 s para mpremote run: dados reais e BMP sem reset por ADC zero.

Executa em RAM, nao grava arquivos e nao reinicia a placa automaticamente.
O host deve executar mpremote reset ao terminar para retomar main.py.
"""
from machine import Pin, SoftI2C
import struct
import time
import ujson
import config
from api_client import enviar
from wifi import conectar
from sensors.bmp280 import BMP280
from sensors.dht22 import SensorDHT22
from sensors.ldr import SensorLDR
from sensors.mq135 import SensorMQ135


class I2CCapturado:
    """Registra o mesmo bloco efetivamente consumido pelo driver original."""

    def __init__(self, barramento):
        self.barramento = barramento
        self.ultimo_raw = None
        self.cal_inicial = None

    def readfrom_mem(self, endereco, registro, quantidade):
        dados = self.barramento.readfrom_mem(endereco, registro, quantidade)
        if registro == 0xF7 and quantidade == 6:
            self.ultimo_raw = bytes(dados)
        elif registro == 0x88 and quantidade == 24:
            self.cal_inicial = bytes(dados)
        return dados

    def writeto_mem(self, endereco, registro, dados):
        return self.barramento.writeto_mem(endereco, registro, dados)


def monitorar():
    inicio = time.ticks_ms()
    duracao_ms = 90000
    intervalo_ms = max(3, min(5, int(getattr(config, "INTERVALO_SEGUNDOS", 5)))) * 1000
    ciclos = 0
    validas = 0
    enviadas = 0
    inicializacoes = 0
    print("INICIO_MONITOR_BMP280", ujson.dumps({
        "duracao_solicitada_ms": duracao_ms, "intervalo_ms": intervalo_ms,
        "sda": 21, "scl": 22, "frequencia_hz": 50000}))
    try:
        bus = SoftI2C(sda=Pin(21), scl=Pin(22), freq=50000, timeout=5000)
        capturado = I2CCapturado(bus)
        outros = [SensorLDR(pino=18), SensorDHT22(pino=4), SensorMQ135(pino=34)]
        bmp = None
        endereco = None
        ultima_tentativa = None
        while time.ticks_diff(time.ticks_ms(), inicio) < duracao_ms:
            rodada = time.ticks_ms()
            ciclos += 1
            capturado.ultimo_raw = None
            erros = []
            dados = {"estacao_id": config.ESTACAO_ID,
                     "temperatura": None, "umidade": None, "gas": None,
                     "temperatura_bmp": None, "pressao": None, "bmp_conectado": False}
            meta = {"tipo": "monitor_bmp280", "ciclo": ciclos,
                    "decorrido_ms": time.ticks_diff(rodada, inicio),
                    "raw6": None, "adc_t": None, "adc_p": None,
                    "cal_cache": None, "cal_inicial_hex": None,
                    "cal_fresca_hex": None, "cal_coincide_cache": None,
                    "id": None, "cfg_f3_f5": None,
                    "driver_retornou_valores": False, "resultado_driver": None, "api_ok": False,
                    "init_neste_ciclo": False, "erros": erros}
            for outro in outros:
                try:
                    dados.update(outro.ler())
                except Exception as erro:
                    erros.append("sensor_" + outro.__class__.__name__ + ": " + repr(erro))

            if bmp is None and (ultima_tentativa is None or
                                time.ticks_diff(rodada, ultima_tentativa) >= 5000):
                ultima_tentativa = rodada
                for candidato in (0x76, 0x77):
                    try:
                        identidade = bus.readfrom_mem(candidato, 0xD0, 1)[0]
                    except OSError:
                        continue
                    if identidade != 0x58:
                        erros.append("id_inesperado_" + hex(candidato) + ": " + hex(identidade))
                        continue
                    endereco = candidato
                    capturado.cal_inicial = None
                    meta["init_neste_ciclo"] = True
                    try:
                        bmp = BMP280(capturado, endereco)
                        inicializacoes += 1
                    except (OSError, ValueError, ZeroDivisionError) as erro:
                        erros.append("inicializacao: " + repr(erro))
                        bmp = None
                    break
                if endereco is None:
                    erros.append("nenhum_bmp280_identificado")

            cache = tuple(bmp.cal) if bmp is not None else None
            if cache is not None:
                meta["cal_cache"] = list(cache)
            if capturado.cal_inicial is not None:
                meta["cal_inicial_hex"] = capturado.cal_inicial.hex()
            if bmp is not None:
                try:
                    temperatura, pressao = bmp.ler()
                    dados.update({"temperatura_bmp": temperatura, "pressao": pressao,
                                  "bmp_conectado": True})
                    meta["driver_retornou_valores"] = True
                    meta["resultado_driver"] = {"temperatura_bmp": temperatura, "pressao": pressao}
                except ValueError as erro:
                    # Preserva o objeto: a proxima aquisicao usa forced 0x55,
                    # sem reiniciar o BMP nem reler sua calibracao em __init__.
                    erros.append("medicao_invalida: " + repr(erro))
                except (OSError, ZeroDivisionError) as erro:
                    erros.append("falha_medicao: " + repr(erro))
                    bmp = None
                    ultima_tentativa = time.ticks_ms()

            raw = capturado.ultimo_raw
            if raw is not None:
                meta["raw6"] = raw.hex()
                if len(raw) == 6:
                    meta["adc_p"] = (raw[0] << 12) | (raw[1] << 4) | (raw[2] >> 4)
                    meta["adc_t"] = (raw[3] << 12) | (raw[4] << 4) | (raw[5] >> 4)

            # Metadados posteriores nao substituem a amostra acima nem o cache.
            consistente = False
            if endereco is not None:
                try:
                    fresca = bus.readfrom_mem(endereco, 0x88, 24)
                    meta["cal_fresca_hex"] = fresca.hex()
                    coeficientes = struct.unpack("<HhhHhhhhhhhh", fresca)
                    meta["cal_coincide_cache"] = cache is not None and coeficientes == cache
                    consistente = (meta["cal_coincide_cache"] and
                                   fresca != bytes(24) and fresca != bytes([255]) * 24 and
                                   coeficientes[0] != 0 and coeficientes[3] != 0)
                    if not consistente:
                        erros.append("calibracao_fresca_nao_confirmada_com_cache")
                except (OSError, ValueError) as erro:
                    erros.append("calibracao_fresca: " + repr(erro))
                try:
                    meta["id"] = bus.readfrom_mem(endereco, 0xD0, 1)[0]
                    meta["cfg_f3_f5"] = bus.readfrom_mem(endereco, 0xF3, 3).hex()
                    if meta["id"] != 0x58:
                        consistente = False
                        erros.append("identidade_posterior_diferente_de_0x58")
                except OSError as erro:
                    consistente = False
                    erros.append("metadados_bus: " + repr(erro))
            if not consistente:
                dados.update({"temperatura_bmp": None, "pressao": None, "bmp_conectado": False})
            if dados["bmp_conectado"]:
                validas += 1

            if "luz" in dados and "estado" in dados:
                try:
                    conectar(config.WIFI_SSID, config.WIFI_PASSWORD, timeout=5)
                    enviar(config.API_URL, config.API_KEY, dados)
                    meta["api_ok"] = True
                    enviadas += 1
                except Exception as erro:
                    # Excecoes de rede/API nao imprimem URL, chave, SSID ou senha.
                    erros.append("envio_api: " + erro.__class__.__name__)
            else:
                erros.append("envio_api_omitido_payload_sem_leitura_ldr")
            meta["endereco"] = hex(endereco) if endereco is not None else None
            meta["inicializacoes"] = inicializacoes
            meta["dados"] = dados
            print(ujson.dumps(meta))
            restantes = duracao_ms - time.ticks_diff(time.ticks_ms(), inicio)
            espera = intervalo_ms - time.ticks_diff(time.ticks_ms(), rodada)
            if restantes > 0 and espera > 0:
                time.sleep_ms(min(restantes, espera))
    finally:
        print("FIM_MONITOR_BMP280", ujson.dumps({
            "duracao_real_ms": time.ticks_diff(time.ticks_ms(), inicio),
            "ciclos": ciclos, "bmp_validas": validas, "api_enviadas": enviadas,
            "inicializacoes": inicializacoes}))
        print("Monitor encerrado; o host deve reiniciar o ESP32 para retomar main.py.")


monitorar()
