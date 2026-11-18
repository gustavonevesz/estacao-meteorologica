import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

class Banco:
    def __init__(self, caminho):
        self.caminho = Path(caminho)

    @contextmanager
    def conectar(self):
        conexao = sqlite3.connect(self.caminho, timeout=10)
        conexao.row_factory = sqlite3.Row
        try:
            with conexao:
                yield conexao
        finally:
            conexao.close()

    def inicializar(self):
        self.caminho.parent.mkdir(parents=True, exist_ok=True)
        with self.conectar() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS leituras (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                estacao_id TEXT NOT NULL, recebido_em TEXT NOT NULL,
                luz INTEGER NOT NULL, estado TEXT NOT NULL,
                temperatura REAL, umidade REAL, gas INTEGER,
                pressao REAL, temperatura_bmp REAL, bmp_conectado INTEGER NOT NULL
            )""")
            db.execute("CREATE INDEX IF NOT EXISTS idx_estacao_id ON leituras(estacao_id, id DESC)")

    def salvar(self, dados):
        valores = dados.model_dump()
        valores["recebido_em"] = datetime.now(timezone.utc).isoformat()
        colunas = list(valores)
        with self.conectar() as db:
            cursor = db.execute(
                "INSERT INTO leituras (" + ",".join(colunas) + ") VALUES (" + ",".join("?" for _ in colunas) + ")",
                [valores[c] for c in colunas],
            )
            return dict(db.execute("SELECT * FROM leituras WHERE id = ?", (cursor.lastrowid,)).fetchone())

    def listar(self, estacao_id=None, limite=100, antes_id=None):
        condicoes, parametros = [], []
        if estacao_id:
            condicoes.append("estacao_id = ?")
            parametros.append(estacao_id)
        if antes_id is not None:
            condicoes.append("id < ?")
            parametros.append(antes_id)
        where = " WHERE " + " AND ".join(condicoes) if condicoes else ""
        with self.conectar() as db:
            return [dict(row) for row in db.execute(
                "SELECT * FROM leituras" + where + " ORDER BY id DESC LIMIT ?", parametros + [limite]
            )]
