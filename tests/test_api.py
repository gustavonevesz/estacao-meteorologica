from fastapi.testclient import TestClient
from backend.main import create_app

DADOS = dict(estacao_id="esp32-01", luz=0, estado="Claro", temperatura=25.5,
             umidade=60, gas=1200, pressao=1013.2, temperatura_bmp=25, bmp_conectado=True)

def test_fluxo_persistencia_e_filtros(tmp_path):
    caminho = tmp_path / "teste.db"
    with TestClient(create_app(caminho, "segredo")) as cliente:
        assert cliente.get("/").status_code == 200
        assert cliente.get("/static/app.js").status_code == 200
        assert cliente.get("/api/leituras/ultima").status_code == 404
        assert cliente.post("/api/leituras", json=DADOS).status_code == 401
        r = cliente.post("/api/leituras", json=DADOS, headers={"X-API-Key":"segredo"})
        assert r.status_code == 201
        assert r.json()["recebido_em"].endswith("+00:00")
        assert r.json()["bmp_conectado"] is True
        segundo = cliente.post("/api/leituras", json={**DADOS, "estacao_id":"outra"}, headers={"X-API-Key":"segredo"}).json()
        assert len(cliente.get("/api/leituras?estacao_id=esp32-01").json()) == 1
        assert len(cliente.get(f"/api/leituras?antes_id={segundo['id']}").json()) == 1
        assert cliente.get("/api/leituras?limite=1001").status_code == 422
        for alteracao in ({"gas":4096}, {"estado":"Escuro"}, {"umidade":101}, {"bmp_conectado":False}):
            assert cliente.post("/api/leituras", json={**DADOS, **alteracao}, headers={"X-API-Key":"segredo"}).status_code == 422
        falha = {**DADOS, "temperatura":None, "umidade":None, "pressao":None, "temperatura_bmp":None, "bmp_conectado":False}
        assert cliente.post("/api/leituras", json=falha, headers={"X-API-Key":"segredo"}).status_code == 201
    with TestClient(create_app(caminho, "segredo")) as cliente:
        assert len(cliente.get("/api/leituras").json()) == 3
        assert cliente.get("/api/leituras/ultima").json()["temperatura"] is None

def test_sem_chave_configurada(tmp_path):
    with TestClient(create_app(tmp_path / "teste.db", "")) as cliente:
        assert cliente.post("/api/leituras", json=DADOS).status_code == 503


def test_chave_errada_retorna_401_e_nao_grava(tmp_path):
    with TestClient(create_app(tmp_path / "teste.db", "segredo")) as cliente:
        r = cliente.post("/api/leituras", json=DADOS, headers={"X-API-Key": "outra"})
        assert r.status_code == 401
        assert cliente.get("/api/leituras").json() == []


def test_impressao_digital_nao_expoe_a_chave():
    from backend.main import impressao_digital
    assert impressao_digital("") == "(vazia)"
    assert impressao_digital("segredo") == impressao_digital("segredo")
    assert impressao_digital("segredo") != impressao_digital("segredo2")
    assert "segredo" not in impressao_digital("segredo")


def test_leitura_sem_campos_obrigatorios_e_rejeitada(tmp_path):
    # Reproduz o payload parcial enviado se um driver do firmware falhar.
    parcial = {k: v for k, v in DADOS.items() if k not in ("luz", "estado")}
    with TestClient(create_app(tmp_path / "teste.db", "segredo")) as cliente:
        assert cliente.post("/api/leituras", json=parcial, headers={"X-API-Key": "segredo"}).status_code == 422
