"""Backup privado recuperavel; usa somente projetos temporarios, nunca a placa."""
import hashlib
import json
from contextlib import closing
from pathlib import Path
import sqlite3

import pytest

from scripts.backup_antes_arduino import criar_backup


@pytest.fixture
def projeto(tmp_path):
    raiz = tmp_path / "projeto"
    raiz.mkdir()
    for pasta in ("backend", "firmware", "frontend", "scripts", "tests", "diagnosticos", ".vscode"):
        (raiz / pasta).mkdir()
        (raiz / pasta / "exemplo.txt").write_text("fonte " + pasta, encoding="utf-8")
    (raiz / ".env").write_text("API_KEY=segredo-apenas-do-teste\n", encoding="utf-8")
    (raiz / "firmware" / "config.py").write_text(
        'WIFI_PASSWORD = "senha-apenas-do-teste"\n', encoding="utf-8")
    for nome in ("README.md", "DIAGNOSTICO_BMP280.md", "requirements.txt",
                 "requirements-dev.txt", ".gitignore", ".env.example"):
        (raiz / nome).write_text("conteudo " + nome, encoding="utf-8")
    (raiz / "data").mkdir()
    with closing(sqlite3.connect(raiz / "data" / "estacao.db")) as db:
        db.execute("CREATE TABLE leituras (id INTEGER PRIMARY KEY, recebido_em TEXT)")
        db.executemany("INSERT INTO leituras VALUES (?, ?)",
                       [(1, "2026-11-11T10:00:00+00:00"), (2, "2026-11-11T10:00:05+00:00")])
        db.commit()
    return raiz


def test_fontes_privadas_manifesto_e_snapshot_integro(projeto, capsys):
    destino = criar_backup(projeto)
    manifesto = json.loads((destino / "manifesto.json").read_text(encoding="utf-8"))
    assert destino.parent == projeto / "backup_esp32"
    assert destino.name.startswith("antes_arduino_")
    for relativo in (".env", "firmware/config.py", "README.md", "requirements.txt",
                     "requirements-dev.txt", ".env.example", ".gitignore", ".vscode/exemplo.txt",
                     "diagnosticos/exemplo.txt"):
        assert (destino / "projeto" / relativo).read_bytes() == (projeto / relativo).read_bytes()
    with closing(sqlite3.connect(destino / "snapshot_estacao.db")) as db:
        assert db.execute("PRAGMA integrity_check").fetchall() == [("ok",)]
        assert db.execute("SELECT COUNT(*) FROM leituras").fetchone()[0] == 2
    assert manifesto["banco"]["leituras"]["quantidade"] == 2
    assert manifesto["banco"]["leituras"]["ultimo_id"] == 2
    assert manifesto["banco"]["integridade"] == "ok"
    assert manifesto["inclui_flash_esp32"] is False
    assert set(manifesto["configuracoes_privadas"]) == {".env", "firmware/config.py"}
    assert manifesto["contagem_arquivos"] == len(manifesto["arquivos"])
    for registro in manifesto["arquivos"]:
        conteudo = (destino / registro["caminho"]).read_bytes()
        assert registro["sha256"] == hashlib.sha256(conteudo).hexdigest()
        assert registro["bytes"] == len(conteudo)
    texto_manifesto = (destino / "manifesto.json").read_text(encoding="utf-8")
    saida = capsys.readouterr()
    assert "segredo-apenas-do-teste" not in texto_manifesto + saida.out + saida.err
    assert "senha-apenas-do-teste" not in texto_manifesto + saida.out + saida.err


def test_nao_copia_ambientes_fotos_cache_nem_o_proprio_backup(projeto):
    for pasta in (".venv", ".tools", "backup_esp32/antigo", "diagnostico_bmp280_fotos",
                  "backend/__pycache__", "scripts/.tools", "frontend/backup_esp32"):
        alvo = projeto / pasta
        alvo.mkdir(parents=True, exist_ok=True)
        (alvo / "sentinela.txt").write_text("nao copiar", encoding="utf-8")
    destino = criar_backup(projeto)
    assert not list(destino.rglob("sentinela.txt"))
    assert not (destino / "projeto" / "data").exists()
    assert not (destino / "projeto" / "backup_esp32").exists()


def test_destino_existente_e_recusado_sem_substituir(projeto):
    destino = projeto / "backup_esp32" / "antes_arduino_existente"
    destino.mkdir(parents=True)
    sentinela = destino / "preservar.txt"
    sentinela.write_text("original", encoding="utf-8")
    with pytest.raises(FileExistsError):
        criar_backup(projeto, destino)
    assert sentinela.read_text(encoding="utf-8") == "original"
    assert list(destino.iterdir()) == [sentinela]


@pytest.mark.parametrize("relativo", ["fora/antes_arduino_teste", "backup_esp32",
                                     "backup_esp32/outro_nome", "backup_esp32/filho/antes_arduino_teste"])
def test_saida_fora_do_destino_exclusivo_e_recusada(projeto, relativo):
    with pytest.raises(ValueError):
        criar_backup(projeto, Path(relativo))
    assert not (projeto / "backup_esp32").exists()


def test_caminho_absoluto_externo_e_recusado(projeto, tmp_path):
    fora = tmp_path / "fora" / "antes_arduino_teste"
    with pytest.raises(ValueError):
        criar_backup(projeto, fora)
    assert not fora.parent.exists()


def test_snapshot_inclui_registro_ainda_no_wal(projeto):
    conexao = sqlite3.connect(projeto / "data" / "estacao.db")
    try:
        assert conexao.execute("PRAGMA journal_mode=WAL").fetchone()[0] == "wal"
        conexao.execute("INSERT INTO leituras VALUES (3, '2026-11-11T10:00:10+00:00')")
        conexao.commit()
        destino = criar_backup(projeto, "backup_esp32/antes_arduino_wal")
        with closing(sqlite3.connect(destino / "snapshot_estacao.db")) as copia:
            assert copia.execute("SELECT MAX(id), COUNT(*) FROM leituras").fetchone() == (3, 3)
            assert copia.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    finally:
        conexao.close()


def test_banco_corrompido_nao_produz_manifesto_de_sucesso(projeto):
    (projeto / "data" / "estacao.db").write_bytes(b"isto nao e um banco SQLite")
    destino = projeto / "backup_esp32" / "antes_arduino_corrompido"
    with pytest.raises(sqlite3.DatabaseError):
        criar_backup(projeto, destino)
    assert not (destino / "manifesto.json").exists()


def test_banco_ausente_interrompe_antes_de_criar_destino(projeto):
    (projeto / "data" / "estacao.db").unlink()
    with pytest.raises(FileNotFoundError, match="Banco"):
        criar_backup(projeto)
    assert not (projeto / "backup_esp32").exists()
