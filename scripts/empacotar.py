"""Cria uma entrega portatil com codigo e documentacao, sem configuracao privada."""
import argparse
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


PASTA_ZIP = "Estação Meteorológica"
PASTAS = ("backend", "firmware", "frontend", "scripts", "tests", "diagnosticos", "assets", ".vscode")
ARQUIVOS = ("README.md", "COMO_EXECUTAR.md", "DIAGNOSTICO_BMP280.md", "RELATORIO_BMP280_PROFESSOR.md",
            "TESTE_ARDUINO_BMP280.md", "RELATORIO_FUNCIONAMENTO_E_RECUPERACAO_BMP280.md",
            "ATALHO_WINDOWS.md", "CHANGELOG.md", "requirements.txt", "requirements-dev.txt", ".gitignore")
MODELO_CONFIG = '''WIFI_SSID = "SUA_REDE"
WIFI_PASSWORD = "SUA_SENHA"
API_URL = "http://192.168.1.100:8000/api/leituras"
API_KEY = "troque-por-uma-chave"
ESTACAO_ID = "esp32-01"
INTERVALO_SEGUNDOS = 5
'''


def criar_zip(raiz, destino):
    raiz, destino = Path(raiz).resolve(), Path(destino).resolve()
    if destino.suffix.lower() != ".zip":
        raise ValueError("O destino deve terminar em .zip")
    caminhos = [raiz / nome for nome in ARQUIVOS]
    for nome in PASTAS:
        caminhos.extend(p for p in (raiz / nome).rglob("*") if p.is_file())
    permitidos = []
    for caminho in caminhos:
        relativo = caminho.relative_to(raiz)
        if any(parte in ("__pycache__", ".pytest_cache", ".venv", ".git", ".tools", "backup_esp32")
               for parte in relativo.parts):
            continue
        if caminho.name in (".env", "config.py", "config.example.py"):
            continue
        if caminho.suffix.lower() in (".pyc", ".db", ".sqlite", ".sqlite3", ".zip", ".bin", ".elf", ".map", ".log"):
            continue
        if caminho.is_symlink():
            continue
        permitidos.append(caminho)
    # Modo x evita substituir uma entrega existente.
    with ZipFile(destino, "x", compression=ZIP_DEFLATED, compresslevel=9) as arquivo:
        for caminho in sorted(permitidos):
            arquivo.write(caminho, PASTA_ZIP + "/" + caminho.relative_to(raiz).as_posix())
        arquivo.writestr(PASTA_ZIP + "/.env.example", "API_KEY=troque-por-uma-chave\n")
        arquivo.writestr(PASTA_ZIP + "/firmware/config.example.py", MODELO_CONFIG)
    with ZipFile(destino) as arquivo:
        erro = arquivo.testzip()
        if erro:
            raise ValueError("Falha de integridade no ZIP: " + erro)
        nomes = arquivo.namelist()
        for privado in ("/.env", "/firmware/config.py"):
            if PASTA_ZIP + privado in nomes:
                raise ValueError("Configuracao privada encontrada na entrega")
        quantidade = len(nomes)
    return quantidade


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", required=True, type=Path)
    args = parser.parse_args()
    total = criar_zip(Path(__file__).resolve().parents[1], args.saida)
    print("ZIP criado:", args.saida.resolve())
    print("Arquivos:", total)
    print("Tamanho:", args.saida.stat().st_size, "bytes")
