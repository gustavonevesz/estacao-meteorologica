"""Testes do atalho: HTTP, processos e navegador sao sempre simulados."""

from contextlib import nullcontext
import io
import json
from pathlib import Path
from types import SimpleNamespace
from urllib.error import HTTPError, URLError
from unittest.mock import Mock

import pytest

from scripts import iniciar_estacao as launcher


OWN_DOCUMENT = {
    "info": {"title": "Estação Meteorológica"},
    "paths": {"/api/leituras": {"post": {}}, "/api/leituras/ultima": {"get": {}}},
}


def response(value):
    return io.BytesIO(json.dumps(value).encode("utf-8"))


def test_identifica_api_com_saude_titulo_e_rotas(monkeypatch):
    request = Mock(side_effect=[response({"status": "ok"}), response(OWN_DOCUMENT)])
    monkeypatch.setattr(launcher, "urlopen", request)
    assert launcher.probe_server() is launcher.ServerState.OWN
    assert [call.args[0].full_url for call in request.call_args_list] == [
        "http://127.0.0.1:8000/api/saude", "http://127.0.0.1:8000/openapi.json"
    ]


@pytest.mark.parametrize("document", [
    {"info": {"title": "Outra API"}, "paths": OWN_DOCUMENT["paths"]},
    {"info": OWN_DOCUMENT["info"], "paths": {"/api/leituras": {"post": {}}}},
    {"info": OWN_DOCUMENT["info"], "paths": {"/api/leituras": {"get": {}}, "/api/leituras/ultima": {"get": {}}}},
])
def test_nao_reaproveita_servico_com_identidade_diferente(monkeypatch, document):
    monkeypatch.setattr(launcher, "urlopen", Mock(side_effect=[response({"status": "ok"}), response(document)]))
    assert launcher.probe_server() is launcher.ServerState.OTHER


def test_http_404_e_outro_servico_ao_inves_de_api_desligada(monkeypatch):
    error = HTTPError("http://127.0.0.1:8000/api/saude", 404, "Not found", {}, io.BytesIO())
    monkeypatch.setattr(launcher, "urlopen", Mock(side_effect=error))
    assert launcher.probe_server() is launcher.ServerState.OTHER


@pytest.mark.parametrize("error,expected", [
    (URLError(ConnectionRefusedError(10061, "refused")), launcher.ServerState.OFFLINE),
    (URLError(TimeoutError("timeout")), launcher.ServerState.UNRESPONSIVE),
])
def test_distingue_porta_desligada_de_servico_sem_resposta(monkeypatch, error, expected):
    monkeypatch.setattr(launcher, "urlopen", Mock(side_effect=error))
    assert launcher.probe_server() is expected


@pytest.fixture
def isolated(monkeypatch):
    lock = Mock(side_effect=lambda root, port: nullcontext())
    browser = Mock(return_value=True)
    spawn = Mock(return_value=SimpleNamespace(poll=lambda: None))
    validation = Mock()
    monkeypatch.setattr(launcher, "startup_lock", lock)
    monkeypatch.setattr(launcher.webbrowser, "open", browser)
    monkeypatch.setattr(launcher, "start_server", spawn)
    monkeypatch.setattr(launcher, "validate_environment", validation)
    monkeypatch.setattr(launcher.time, "sleep", lambda seconds: None)
    return SimpleNamespace(lock=lock, browser=browser, spawn=spawn, validation=validation)


def test_servidor_existente_abre_painel_sem_dependencias_ou_novo_processo(monkeypatch, isolated, tmp_path):
    monkeypatch.setattr(launcher, "probe_server", Mock(return_value=launcher.ServerState.OWN))
    launcher.launch_station(tmp_path)
    isolated.browser.assert_called_once_with("http://127.0.0.1:8000/", new=2)
    isolated.spawn.assert_not_called()
    isolated.validation.assert_not_called()
    isolated.lock.assert_called_once_with(tmp_path.resolve(), 8000)


@pytest.mark.parametrize("state", [launcher.ServerState.OTHER, launcher.ServerState.UNRESPONSIVE])
def test_servico_alheio_ou_timeout_nao_inicia_segunda_api(monkeypatch, isolated, tmp_path, state):
    monkeypatch.setattr(launcher, "probe_server", Mock(return_value=state))
    with pytest.raises(launcher.LauncherError):
        launcher.launch_station(tmp_path)
    isolated.spawn.assert_not_called()
    isolated.browser.assert_not_called()


def test_partida_fria_aguarda_identidade_antes_de_abrir(monkeypatch, isolated, tmp_path):
    monkeypatch.setattr(launcher, "probe_server", Mock(side_effect=[
        launcher.ServerState.OFFLINE, launcher.ServerState.OFFLINE, launcher.ServerState.OWN
    ]))
    launcher.launch_station(tmp_path, port=18000)
    isolated.validation.assert_called_once_with(tmp_path.resolve())
    isolated.spawn.assert_called_once_with(tmp_path.resolve(), 18000)
    isolated.browser.assert_called_once_with("http://127.0.0.1:18000/", new=2)


def test_timeout_da_partida_preserva_processo_e_informa_console(monkeypatch):
    process = Mock()
    process.poll.return_value = None
    monkeypatch.setattr(launcher, "probe_server", Mock(return_value=launcher.ServerState.UNRESPONSIVE))
    monkeypatch.setattr(launcher.time, "monotonic", Mock(side_effect=[0, 0, 1, 2]))
    monkeypatch.setattr(launcher.time, "sleep", lambda seconds: None)
    with pytest.raises(launcher.LauncherError, match="console|janela"):
        launcher.wait_for_server(process, 8000, timeout=2)
    process.terminate.assert_not_called()
    process.kill.assert_not_called()


def test_processo_encerrado_antes_de_pronto(monkeypatch):
    monkeypatch.setattr(launcher, "probe_server", Mock(return_value=launcher.ServerState.OFFLINE))
    with pytest.raises(launcher.LauncherError, match="encerrou"):
        launcher.wait_for_server(SimpleNamespace(poll=lambda: 1), 8000)


def test_popen_usa_python_do_projeto_console_novo_e_porta_explicita(monkeypatch, tmp_path):
    popen = Mock()
    monkeypatch.setattr(launcher.subprocess, "Popen", popen)
    launcher.start_server(tmp_path, 18000)
    command = popen.call_args.args[0]
    assert command == [str(tmp_path / ".venv" / "Scripts" / "python.exe"), "-u",
                       str(Path(launcher.__file__).resolve()), "--servidor", "--raiz", str(tmp_path), "--porta", "18000"]
    assert popen.call_args.kwargs == {"cwd": str(tmp_path), "creationflags": launcher.CREATE_NEW_CONSOLE}


def test_erro_do_navegador_mantem_api_e_mostra_endereco(monkeypatch):
    monkeypatch.setattr(launcher.webbrowser, "open", Mock(return_value=False))
    with pytest.raises(launcher.LauncherError, match="http://127.0.0.1:8000/"):
        launcher.open_panel(8000)


def test_ambiente_sem_env_informa_arquivo_sem_ler_segredos(tmp_path):
    (tmp_path / "backend").mkdir()
    (tmp_path / "backend" / "main.py").touch()
    with pytest.raises(launcher.LauncherError, match=r"\.env"):
        launcher.validate_environment(tmp_path)


def test_mutex_distingue_pasta_e_porta(tmp_path):
    assert launcher._mutex_name(tmp_path, 8000) == launcher._mutex_name(tmp_path, 8000)
    assert launcher._mutex_name(tmp_path, 8000) != launcher._mutex_name(tmp_path, 18000)
    assert launcher._mutex_name(tmp_path, 8000) != launcher._mutex_name(tmp_path / "outro", 8000)


def test_modo_servidor_recebe_raiz_e_porta_sem_abrir_navegador(monkeypatch, tmp_path):
    server = Mock(return_value=0)
    browser = Mock()
    monkeypatch.setattr(launcher, "run_server", server)
    monkeypatch.setattr(launcher.webbrowser, "open", browser)
    assert launcher.main(["--servidor", "--raiz", str(tmp_path), "--porta", "18000"]) == 0
    server.assert_called_once_with(tmp_path, 18000)
    browser.assert_not_called()


def test_erro_e_apresentado_por_gui_sem_traceback(monkeypatch):
    monkeypatch.setattr(launcher, "launch_station", Mock(side_effect=launcher.LauncherError("Porta ocupada")))
    message = Mock()
    monkeypatch.setattr(launcher, "show_error", message)
    assert launcher.main([]) == 1
    message.assert_called_once_with("Porta ocupada")


def test_console_chama_uvicorn_com_env_raiz_e_porta_explicita(monkeypatch, tmp_path):
    uvicorn = SimpleNamespace(run=Mock())
    validation = Mock()
    directory = Mock()
    monkeypatch.setitem(launcher.sys.modules, "uvicorn", uvicorn)
    monkeypatch.setattr(launcher, "validate_environment", validation)
    monkeypatch.setattr(launcher, "_console_title", Mock())
    monkeypatch.setattr(launcher.os, "chdir", directory)
    monkeypatch.setattr(launcher.sys, "path", list(launcher.sys.path))
    assert launcher.run_server(tmp_path, 18000) == 0
    validation.assert_called_once_with(tmp_path.resolve(), server_mode=True)
    directory.assert_called_once_with(tmp_path.resolve())
    assert launcher.sys.path[0] == str(tmp_path.resolve())
    uvicorn.run.assert_called_once_with(
        "backend.main:app", host="0.0.0.0", port=18000,
        env_file=str(tmp_path.resolve() / ".env"), reload=False,
    )


def test_erro_do_console_fica_visivel_sem_imprimir_mensagem_privada(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(launcher, "validate_environment", Mock(side_effect=RuntimeError("conteudo-privado")))
    monkeypatch.setattr(launcher, "_console_title", Mock())
    pause = Mock(return_value="")
    monkeypatch.setattr("builtins.input", pause)
    assert launcher.run_server(tmp_path, 18000) == 1
    output = capsys.readouterr().out
    assert "conteudo-privado" not in output
    assert "RuntimeError" in output
    pause.assert_called_once()
