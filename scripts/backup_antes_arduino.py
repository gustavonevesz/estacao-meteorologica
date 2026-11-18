"""Backup PRIVADO das fontes/configuracoes e SQLite; nao acessa a placa.

Exemplo, a partir da raiz do projeto:
    python scripts/backup_antes_arduino.py
    python scripts/backup_antes_arduino.py --saida backup_esp32/antes_arduino_teste

Este backup inclui segredos locais. Nao deve acompanhar o ZIP compartilhavel.
A imagem integral da flash precisa ser obtida separadamente com esptool.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import time


DIRETORIOS = ("backend", "firmware", "frontend", "scripts", "tests", "diagnosticos", ".vscode")
ARQUIVOS_PRIVADOS = (".env", ".env.example", ".gitignore")
IGNORADOS = {"__pycache__", ".pytest_cache", ".venv", "venv", ".tools",
             "backup_esp32", "diagnostico_bmp280_fotos", "node_modules", ".git"}
PREFIXO = "antes_arduino_"


def _recusar_link(caminho):
    junction = getattr(caminho, "is_junction", lambda: False)()
    atributos = getattr(caminho.lstat(), "st_file_attributes", 0)
    # Tambem protege junctions no Python anterior a Path.is_junction().
    diretorio_reparse = caminho.is_dir() and bool(atributos & 0x400)
    if caminho.is_symlink() or junction or diretorio_reparse:
        raise ValueError("Link ou junction nao permitido no backup: " + str(caminho))


def _percorrer(diretorio):
    _recusar_link(diretorio)
    for entrada in sorted(diretorio.iterdir(), key=lambda item: item.name):
        if entrada.name in IGNORADOS or entrada.suffix.lower() in (".pyc", ".pyo"):
            continue
        _recusar_link(entrada)
        if entrada.is_dir():
            yield from _percorrer(entrada)
        elif entrada.is_file():
            yield entrada


def _fontes(raiz):
    for nome in DIRETORIOS:
        diretorio = raiz / nome
        if diretorio.exists():
            if not diretorio.is_dir():
                raise ValueError("Esperado diretorio: " + str(diretorio))
            yield from _percorrer(diretorio)
    for entrada in sorted(raiz.iterdir(), key=lambda item: item.name):
        documento = entrada.suffix.lower() == ".md"
        dependencias = entrada.name.startswith("requirements") and entrada.suffix == ".txt"
        if entrada.name in ARQUIVOS_PRIVADOS or documento or dependencias:
            _recusar_link(entrada)
            if entrada.is_file():
                yield entrada


def _destino_seguro(raiz, saida):
    base = raiz / "backup_esp32"
    if os.path.lexists(base):
        _recusar_link(base)
        if not base.is_dir():
            raise ValueError("backup_esp32 precisa ser um diretorio")
    if saida is None:
        nome = PREFIXO + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%fZ")
        destino = base / nome
    else:
        destino = Path(saida)
        if not destino.is_absolute():
            destino = raiz / destino
    if destino.parent.resolve() != base.resolve():
        raise ValueError("A saida deve ser filha direta de backup_esp32")
    if not destino.name.startswith(PREFIXO) or len(destino.name) <= len(PREFIXO):
        raise ValueError("O nome da saida deve comecar com antes_arduino_")
    if os.path.lexists(destino):
        raise FileExistsError("Destino ja existe; nenhum arquivo sera substituido: " + str(destino))
    return base, destino.resolve()


def _snapshot_sqlite(origem, destino):
    inicio = time.monotonic()

    def progresso(status, restantes, total):
        if time.monotonic() - inicio > 60:
            raise TimeoutError("Backup SQLite excedeu 60 segundos")

    fonte = sqlite3.connect(origem.as_uri() + "?mode=ro", uri=True, timeout=10)
    copia = None
    try:
        copia = sqlite3.connect(destino)
        fonte.backup(copia, pages=128, progress=progresso, sleep=0.05)
        resultado = copia.execute("PRAGMA integrity_check").fetchall()
        if resultado != [("ok",)]:
            raise sqlite3.DatabaseError("A verificacao de integridade do snapshot falhou")
        metadados = {"origem": "data/estacao.db", "snapshot": destino.name,
                     "integridade": "ok"}
        tabela = copia.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='leituras'"
        ).fetchone()
        if tabela:
            colunas = {linha[1] for linha in copia.execute("PRAGMA table_info(leituras)")}
            leituras = {"quantidade": copia.execute("SELECT COUNT(*) FROM leituras").fetchone()[0]}
            if "id" in colunas:
                leituras["ultimo_id"] = copia.execute("SELECT MAX(id) FROM leituras").fetchone()[0]
            if "recebido_em" in colunas:
                leituras["ultimo_recebido_em"] = copia.execute(
                    "SELECT MAX(recebido_em) FROM leituras"
                ).fetchone()[0]
            metadados["leituras"] = leituras
        return metadados
    finally:
        if copia is not None:
            copia.close()
        fonte.close()


def _metadados_arquivo(arquivo, destino):
    digest = hashlib.sha256()
    with arquivo.open("rb") as entrada:
        for bloco in iter(lambda: entrada.read(1024 * 1024), b""):
            digest.update(bloco)
    return {"caminho": arquivo.relative_to(destino).as_posix(),
            "bytes": arquivo.stat().st_size, "sha256": digest.hexdigest()}


def criar_backup(raiz=None, saida=None):
    """Cria um destino novo e devolve seu Path; nunca substitui um backup.

    A origem do banco e data/estacao.db. Falhas deixam arquivos parciais, mas
    nao um manifesto de sucesso; nenhuma exclusao automatica e realizada.
    """
    raiz = Path(raiz or Path(__file__).resolve().parents[1]).resolve(strict=True)
    base, destino = _destino_seguro(raiz, saida)
    banco = raiz / "data" / "estacao.db"
    if not banco.is_file():
        raise FileNotFoundError("Banco data/estacao.db nao encontrado; backup interrompido")
    _recusar_link(banco)
    # Materializar a lista antes de criar a pasta evita incluir o proprio backup.
    selecionados = list(_fontes(raiz))
    base.mkdir(exist_ok=True)
    destino.mkdir(mode=0o700, exist_ok=False)
    for origem in selecionados:
        alvo = destino / "projeto" / origem.relative_to(raiz)
        alvo.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(origem, alvo, follow_symlinks=False)
    metadados_banco = _snapshot_sqlite(banco, destino / "snapshot_estacao.db")
    arquivos = [_metadados_arquivo(arquivo, destino)
                for arquivo in sorted(destino.rglob("*")) if arquivo.is_file()]
    manifesto = {
        "versao": 1,
        "tipo": "backup_privado_projeto_antes_arduino",
        "criado_em_utc": datetime.now(timezone.utc).isoformat(),
        "raiz_projeto": str(raiz),
        "inclui_flash_esp32": False,
        "configuracoes_privadas": [nome for nome in (".env", "firmware/config.py")
                                  if (destino / "projeto" / nome).is_file()],
        "banco": metadados_banco,
        "contagem_arquivos": len(arquivos),
        "total_bytes": sum(arquivo["bytes"] for arquivo in arquivos),
        "arquivos": arquivos,
    }
    # O manifesto e gravado por ultimo e nao inclui um hash circular de si mesmo.
    with (destino / "manifesto.json").open("x", encoding="utf-8") as arquivo:
        json.dump(manifesto, arquivo, ensure_ascii=False, indent=2)
        arquivo.write("\n")
    return destino


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", type=Path,
                        help="Pasta nova backup_esp32/antes_arduino_NOME, relativa a raiz do projeto")
    argumentos = parser.parse_args()
    try:
        destino = criar_backup(saida=argumentos.saida)
    except (OSError, ValueError, sqlite3.Error) as erro:
        parser.exit(1, "Backup nao concluido: " + str(erro) + "\n")
    manifesto = json.loads((destino / "manifesto.json").read_text(encoding="utf-8"))
    print("Backup PRIVADO criado:", destino)
    print("Arquivos:", manifesto["contagem_arquivos"], "- SQLite: ok - Flash ESP32: nao incluida")


if __name__ == "__main__":
    main()
