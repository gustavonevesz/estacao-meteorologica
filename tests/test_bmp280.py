"""Testa compensacao, amostras invalidas e timeout sem depender da placa."""
import importlib.util
import struct
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


CALIBRACAO = (27504, 26435, -1000, 36477, -10685, 3024,
              2855, 140, -7, 15500, -14600, 6000)


class Relogio:
    def __init__(self):
        self.agora = 0

    def ticks_ms(self):
        return self.agora

    def sleep_ms(self, intervalo):
        self.agora += intervalo

    @staticmethod
    def ticks_diff(atual, anterior):
        return atual - anterior


class Barramento:
    def __init__(self, temperatura=519888, pressao=415148, calibracao=CALIBRACAO):
        self.temperatura = temperatura
        self.pressao = pressao
        self.calibracao = calibracao
        self.ocupado = False
        self.controle = 0

    def writeto_mem(self, endereco, registro, dados):
        if registro == 0xF4:
            self.controle = dados[0]

    def readfrom_mem(self, endereco, registro, quantidade):
        if endereco != 0x76:
            raise OSError("Dispositivo ausente")
        if registro == 0xD0:
            return bytes([0x58])
        if registro == 0x88:
            return struct.pack("<HhhHhhhhhhhh", *self.calibracao)
        if registro == 0xF3:
            return bytes([8 if self.ocupado else 0])
        if registro == 0xF4:
            return bytes([self.controle if self.ocupado else self.controle & ~3])
        if registro == 0xF7:
            return ((self.pressao << 4).to_bytes(3, "big")
                    + (self.temperatura << 4).to_bytes(3, "big"))
        raise AssertionError("Registrador inesperado")


@pytest.fixture
def driver(monkeypatch):
    monkeypatch.setitem(sys.modules, "machine", SimpleNamespace(Pin=lambda pino: pino,
                                                               SoftI2C=None))
    caminho = Path(__file__).resolve().parents[1] / "firmware" / "sensors" / "bmp280.py"
    spec = importlib.util.spec_from_file_location("bmp280_em_teste", caminho)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    modulo.time = Relogio()
    return modulo


def test_compensacao_com_vetor_de_referencia(driver):
    sensor = driver.BMP280(Barramento(), 0x76)
    assert sensor.ler() == (25.1, 1006.53)


@pytest.mark.parametrize("temperatura", [0, 0x80000, 0xFFFFF])
def test_amostra_termica_invalida_nao_produz_pressao(driver, temperatura):
    sensor = driver.BMP280(Barramento(temperatura=temperatura), 0x76)
    with pytest.raises(ValueError, match="Temperatura bruta invalida"):
        sensor.ler()


def test_sensor_ocupado_tem_timeout(driver):
    barramento = Barramento()
    sensor = driver.BMP280(barramento, 0x76)
    barramento.ocupado = True
    with pytest.raises(OSError, match="timeout"):
        sensor.ler()
    assert driver.time.agora < 1100


def test_calibracao_zerada_e_rejeitada(driver):
    with pytest.raises(ValueError, match="Coeficientes"):
        driver.BMP280(Barramento(calibracao=(0,) * 12), 0x76)


def test_falha_bmp_preserva_payload_valido_e_recupera(driver, tmp_path):
    from fastapi.testclient import TestClient
    from backend.main import create_app

    barramento = Barramento(temperatura=0)
    driver.SoftI2C = lambda **kwargs: barramento
    sensor = driver.SensorBMP280(scl=22, sda=21)
    dados = dict(estacao_id="teste-bmp", luz=0, estado="Claro", temperatura=23,
                 umidade=60, gas=1200)
    falha = sensor.ler()
    assert falha == {"temperatura_bmp": None, "pressao": None, "bmp_conectado": False}
    with TestClient(create_app(tmp_path / "bmp.db", "teste")) as cliente:
        resposta = cliente.post("/api/leituras", json={**dados, **falha},
                                headers={"X-API-Key": "teste"})
        assert resposta.status_code == 201
        assert resposta.json()["temperatura"] == 23
        assert resposta.json()["pressao"] is None
    barramento.temperatura = 519888
    driver.time.sleep_ms(5000)
    recuperado = sensor.ler()
    assert recuperado["bmp_conectado"] is True
    assert recuperado["pressao"] == 1006.53
