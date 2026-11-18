"""Verifica o log de demonstracao sem abrir serial nem transmitir pela rede."""
import json
from pathlib import Path
import runpy
import sys
from types import SimpleNamespace

import pytest


class FimDoCiclo(Exception):
    pass


def executar_ciclo(monkeypatch, erro_envio=None):
    enviados = []
    esperas = []

    def esperar(segundos):
        esperas.append(segundos)
        raise FimDoCiclo()

    def enviar(url, chave, dados):
        if erro_envio:
            raise erro_envio
        enviados.append(dict(dados))

    monkeypatch.setitem(sys.modules, "time", SimpleNamespace(sleep=esperar))
    monkeypatch.setitem(sys.modules, "ujson", SimpleNamespace(dumps=json.dumps))
    monkeypatch.setitem(sys.modules, "config", SimpleNamespace(
        ESTACAO_ID="esp32-01", WIFI_SSID="rede-teste", WIFI_PASSWORD="senha-privada-teste",
        API_URL="http://192.0.2.1:8000/api/leituras", API_KEY="chave-privada-teste",
        INTERVALO_SEGUNDOS=1))
    monkeypatch.setitem(sys.modules, "wifi", SimpleNamespace(
        conectar=lambda *args: SimpleNamespace(ifconfig=lambda: ("192.0.2.2",))))
    monkeypatch.setitem(sys.modules, "api_client", SimpleNamespace(enviar=enviar))
    sensores = {
        "ldr": ("SensorLDR", {"luz": 0, "estado": "Claro"}),
        "dht22": ("SensorDHT22", {"temperatura": 24.5, "umidade": 68.2}),
        "mq135": ("SensorMQ135", {"gas": 234}),
        "bmp280": ("SensorBMP280", {
            "pressao": None, "temperatura_bmp": None, "bmp_conectado": False}),
    }
    for modulo, (nome, leitura) in sensores.items():
        classe = type(nome, (), {
            "__init__": lambda self, **kwargs: None,
            "ler": lambda self, valor=leitura: dict(valor),
        })
        monkeypatch.setitem(sys.modules, "sensors." + modulo, SimpleNamespace(**{nome: classe}))
    arquivo = Path(__file__).resolve().parents[1] / "firmware" / "main.py"
    with pytest.raises(FimDoCiclo):
        runpy.run_path(str(arquivo), run_name="__main__")
    return enviados, esperas


def test_payload_do_log_e_json_e_corresponde_ao_enviado(monkeypatch, capsys):
    enviados, esperas = executar_ciclo(monkeypatch)
    texto = capsys.readouterr().out
    linha = next(l for l in texto.splitlines() if l.startswith("[PAYLOAD JSON] "))
    payload = json.loads(linha.removeprefix("[PAYLOAD JSON] "))
    assert payload == enviados[0]
    assert payload["bmp_conectado"] is False
    assert payload["pressao"] is None
    assert '"bmp_conectado": false' in linha
    assert '"pressao": null' in linha
    assert "[WIFI] Conectado | IP: 192.0.2.2" in texto
    assert "[HTTP] 201 Created" in texto
    assert "chave-privada-teste" not in texto
    assert "senha-privada-teste" not in texto
    assert esperas == [3]


@pytest.mark.parametrize("erro", [OSError("HTTP 401"), OSError("conexao recusada")])
def test_falha_de_envio_nao_e_anunciada_como_sucesso(monkeypatch, capsys, erro):
    enviados, esperas = executar_ciclo(monkeypatch, erro_envio=erro)
    texto = capsys.readouterr().out
    assert enviados == []
    assert "201 Created" not in texto
    assert "Falha no envio; nova tentativa" in texto
    assert esperas == [3]
