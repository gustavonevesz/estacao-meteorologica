from pathlib import Path
from zipfile import ZipFile

import pytest

from scripts.empacotar import PASTA_ZIP, criar_zip


def test_entrega_preserva_frontend_e_exclui_configuracoes_privadas(tmp_path):
    raiz = Path(__file__).resolve().parents[1]
    destino = tmp_path / "entrega.zip"
    criar_zip(raiz, destino)
    with ZipFile(destino) as arquivo:
        assert arquivo.testzip() is None
        nomes = arquivo.namelist()
        assert PASTA_ZIP + "/COMO_EXECUTAR.md" in nomes
        assert PASTA_ZIP + "/ATALHO_WINDOWS.md" in nomes
        assert PASTA_ZIP + "/scripts/iniciar_estacao.py" in nomes
        assert PASTA_ZIP + "/scripts/criar_atalho.ps1" in nomes
        assert PASTA_ZIP + "/assets/estacao-meteorologica.svg" in nomes
        assert PASTA_ZIP + "/assets/estacao-meteorologica.ico" in nomes
        assert PASTA_ZIP + "/TESTE_ARDUINO_BMP280.md" in nomes
        assert PASTA_ZIP + "/RELATORIO_FUNCIONAMENTO_E_RECUPERACAO_BMP280.md" in nomes
        assert PASTA_ZIP + "/diagnosticos/referencia_bmp280_20261111/manifesto_sha256.json" in nomes
        assert PASTA_ZIP + "/diagnosticos/arduino_bmp280/arduino_bmp280.ino" in nomes
        assert PASTA_ZIP + "/firmware/config.py" not in nomes
        assert PASTA_ZIP + "/.env" not in nomes
        assert not any("/data/" in n or "/backup_esp32/" in n or "/.venv/" in n or "/.tools/" in n
                       for n in nomes)
        assert not any(n.lower().endswith((".bin", ".elf", ".map", ".log")) for n in nomes)
        assert arquivo.read(PASTA_ZIP + "/frontend/index.html") == (raiz / "frontend/index.html").read_bytes()
        assert arquivo.read(PASTA_ZIP + "/frontend/favicon.svg") == (raiz / "assets/estacao-meteorologica.svg").read_bytes()
        modelo = arquivo.read(PASTA_ZIP + "/firmware/config.example.py").decode("utf-8")
        assert 'WIFI_PASSWORD = "SUA_SENHA"' in modelo
        assert 'API_KEY = "troque-por-uma-chave"' in modelo


def test_empacotamento_nao_substitui_arquivo_existente(tmp_path):
    raiz = Path(__file__).resolve().parents[1]
    destino = tmp_path / "existente.zip"
    destino.write_bytes(b"entrega anterior")
    with pytest.raises(FileExistsError):
        criar_zip(raiz, destino)
    assert destino.read_bytes() == b"entrega anterior"
