import hashlib
import logging
import os
import secrets
from contextlib import asynccontextmanager
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from backend.database import Banco
from backend.schemas import LeituraEntrada, LeituraSaida

ROOT = Path(__file__).resolve().parent.parent
log = logging.getLogger("uvicorn.error")

# override=True: o .env passa a ser a unica fonte da chave. Sem isso, uma variavel
# $env:API_KEY esquecida em outra sessao do terminal vence o arquivo e gera 401 "misterioso".
load_dotenv(ROOT / ".env", override=True)


def impressao_digital(chave):
    """Identificador curto e nao reversivel na pratica para comparar chaves sem expo-las."""
    return hashlib.sha256(chave.encode()).hexdigest()[:6] if chave else "(vazia)"


def create_app(db_path=None, api_key=None):
    banco = Banco(db_path or os.getenv("DATABASE_PATH", str(ROOT / "data" / "estacao.db")))
    chave = api_key if api_key is not None else os.getenv("API_KEY", "")

    @asynccontextmanager
    async def lifespan(app):
        banco.inicializar()
        if chave:
            log.info("API_KEY carregada (impressao digital %s)", impressao_digital(chave))
        else:
            log.warning("API_KEY ausente: POST /api/leituras respondera 503. Verifique o .env")
        yield

    app = FastAPI(title="Estação Meteorológica", version="1.0.0", lifespan=lifespan)
    app.mount("/static", StaticFiles(directory=ROOT / "frontend"), name="static")

    @app.get("/", include_in_schema=False)
    def painel():
        return FileResponse(ROOT / "frontend" / "index.html")

    @app.get("/api/saude")
    def saude():
        return {"status": "ok"}

    @app.post("/api/leituras", response_model=LeituraSaida, status_code=201)
    def criar(dados: LeituraEntrada, x_api_key: str = Header(default="")):
        if not chave:
            raise HTTPException(503, "Configure API_KEY no servidor para receber leituras")
        if not secrets.compare_digest(x_api_key.encode(), chave.encode()):
            # Compare as impressoes com a impressao digital do firmware para separar
            # "chave diferente" de "processo com chave antiga na memoria".
            log.warning("Chave rejeitada: recebida=%s esperada=%s",
                        impressao_digital(x_api_key), impressao_digital(chave))
            raise HTTPException(401, "Chave inválida")
        return banco.salvar(dados)

    @app.get("/api/leituras", response_model=list[LeituraSaida])
    def listar(estacao_id: str | None = Query(default=None, max_length=64),
               limite: int = Query(default=100, ge=1, le=1000),
               antes_id: int | None = Query(default=None, ge=1)):
        return banco.listar(estacao_id, limite, antes_id)

    @app.get("/api/leituras/ultima", response_model=LeituraSaida)
    def ultima(estacao_id: str | None = Query(default=None, max_length=64)):
        dados = banco.listar(estacao_id, 1)
        if not dados:
            raise HTTPException(404, "Nenhuma leitura recebida")
        return dados[0]

    return app

app = create_app()
