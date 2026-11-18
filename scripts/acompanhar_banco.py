"""Exibe leituras persistidas no SQLite; abre o banco exclusivamente para leitura."""
from __future__ import annotations

import argparse
from contextlib import closing
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sqlite3
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
COLUNAS = ("id, recebido_em, estacao_id, temperatura, umidade, gas, pressao, "
           "temperatura_bmp, bmp_conectado, luz, estado")
SQL_NOVAS = ("SELECT " + COLUNAS + " FROM leituras "
             "WHERE estacao_id = ? AND id > ? ORDER BY id ASC LIMIT 50")
FUSO = timezone(timedelta(hours=-3))


def exibir(linha, origem, mostrar_json=False):
    horario = datetime.fromisoformat(linha["recebido_em"]).astimezone(FUSO)

    def valor(campo):
        numero = linha[campo]
        return "--" if numero is None else str(numero)

    print(f"[{origem}] ID {linha['id']} | {horario:%d/%m %H:%M:%S} UTC-3 | "
          f"T={valor('temperatura')} C | U={valor('umidade')} % | "
          f"P={valor('pressao')} hPa | gas={valor('gas')} ADC | "
          f"BMP={bool(linha['bmp_conectado'])}", flush=True)
    if mostrar_json:
        registro = dict(linha)
        registro["bmp_conectado"] = bool(registro["bmp_conectado"])
        print("  Registro persistido: " + json.dumps(registro, ensure_ascii=False), flush=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--banco", type=Path, default=ROOT / "data" / "estacao.db")
    parser.add_argument("--estacao", default="esp32-01")
    parser.add_argument("--intervalo", type=float, default=2.0)
    parser.add_argument("--limite", type=int, default=5, help="Registros historicos iniciais")
    parser.add_argument("--uma-vez", action="store_true", help="Consulta e encerra")
    parser.add_argument("--json", action="store_true", help="Exibe tambem o registro em JSON")
    args = parser.parse_args(argv)
    if args.intervalo < 0.2 or not 1 <= args.limite <= 100:
        parser.error("Use intervalo >= 0.2 e limite entre 1 e 100")
    caminho = args.banco.resolve()
    if not caminho.is_file():
        print("Banco nao encontrado. Inicie a API para criar o banco; nenhuma base foi criada por este monitor.",
              file=sys.stderr)
        return 1
    try:
        # mode=ro impede inclusive criar um banco vazio por engano.
        with closing(sqlite3.connect(caminho.as_uri() + "?mode=ro", uri=True,
                                     isolation_level=None, timeout=3)) as banco:
            banco.row_factory = sqlite3.Row
            banco.execute("PRAGMA query_only = ON")
            print("SQLITE | consulta somente leitura | estacao=" + args.estacao, flush=True)
            print("Banco: " + str(caminho), flush=True)
            print("SQL: " + SQL_NOVAS, flush=True)
            print("Parametros: estacao e ultimo ID exibido (sem interpolar dados na SQL).", flush=True)
            total = banco.execute("SELECT COUNT(*) FROM leituras WHERE estacao_id = ?",
                                  (args.estacao,)).fetchone()[0]
            print(f"Registros persistidos nesta estacao: {total}", flush=True)
            ultimas = banco.execute("SELECT " + COLUNAS + " FROM leituras "
                                   "WHERE estacao_id = ? ORDER BY id DESC LIMIT ?",
                                   (args.estacao, args.limite)).fetchall()
            ultimo_id = 0
            print("HISTORICO: as linhas abaixo ja existiam ao abrir a consulta.", flush=True)
            for linha in reversed(ultimas):
                exibir(linha, "HISTORICO", args.json)
                ultimo_id = linha["id"]
            if args.uma_vez:
                return 0
            print("AO VIVO: aguardando novos INSERTs; Ctrl+C encerra apenas esta consulta.", flush=True)
            while True:
                novas = banco.execute(SQL_NOVAS, (args.estacao, ultimo_id)).fetchall()
                for linha in novas:
                    exibir(linha, "NOVO INSERT", args.json)
                    ultimo_id = linha["id"]
                time.sleep(args.intervalo)
    except KeyboardInterrupt:
        print("\nConsulta encerrada. O servidor e o ESP32 continuam independentes.")
        return 0
    except (sqlite3.Error, OSError, ValueError) as erro:
        print("Nao foi possivel consultar o banco: " + str(erro), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
