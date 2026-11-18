"""Abre o painel e inicia a API local somente quando ela ainda nao esta ativa.

O atalho usa pythonw para este bootstrap. O servidor usa python.exe em outro
console e permanece aberto ate Ctrl+C. Este modulo nao importa o backend.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import ctypes
from ctypes import wintypes
from enum import Enum
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import webbrowser


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PORT = 8000
START_TIMEOUT_SECONDS = 30.0
# O Windows pode levar cerca de 2 s para informar conexao recusada no loopback.
HTTP_TIMEOUT_SECONDS = 3.0
CREATE_NEW_CONSOLE = getattr(subprocess, "CREATE_NEW_CONSOLE", 0x00000010)


class LauncherError(Exception):
    """Erro que pode ser mostrado ao usuario sem incluir configuracoes privadas."""


class ServerState(Enum):
    OWN = "estacao"
    OFFLINE = "desligado"
    OTHER = "outro_servico"
    UNRESPONSIVE = "sem_confirmacao"


def origin(port: int = DEFAULT_PORT) -> str:
    return f"http://127.0.0.1:{port}"


def _get_json(url: str, timeout: float):
    request = Request(url, headers={"Accept": "application/json", "Cache-Control": "no-cache"})
    with urlopen(request, timeout=timeout) as response:
        body = response.read(1024 * 1024 + 1)
        if len(body) > 1024 * 1024:
            raise ValueError("Resposta maior que o limite da verificacao local")
        return json.loads(body.decode("utf-8"))


def probe_server(port: int = DEFAULT_PORT, timeout: float = HTTP_TIMEOUT_SECONDS) -> ServerState:
    """Reconhece a API por saude, titulo e duas rotas; nao usa nenhuma chave."""
    try:
        health = _get_json(origin(port) + "/api/saude", timeout)
        if not isinstance(health, dict) or health.get("status") != "ok":
            return ServerState.OTHER
        document = _get_json(origin(port) + "/openapi.json", timeout)
        if not isinstance(document, dict):
            return ServerState.OTHER
        info, paths = document.get("info"), document.get("paths")
        if not isinstance(info, dict) or info.get("title") != "Estação Meteorológica":
            return ServerState.OTHER
        if not isinstance(paths, dict):
            return ServerState.OTHER
        readings, latest = paths.get("/api/leituras"), paths.get("/api/leituras/ultima")
        if not isinstance(readings, dict) or not isinstance(latest, dict):
            return ServerState.OTHER
        return ServerState.OWN if "post" in readings and "get" in latest else ServerState.OTHER
    except HTTPError as error:
        error.close()
        return ServerState.OTHER
    except URLError as error:
        reason = error.reason
        if isinstance(reason, ConnectionRefusedError) or getattr(reason, "errno", None) in (61, 111, 10061):
            return ServerState.OFFLINE
        return ServerState.UNRESPONSIVE
    except ConnectionRefusedError:
        return ServerState.OFFLINE
    except (TimeoutError, OSError):
        return ServerState.UNRESPONSIVE
    except (ValueError, UnicodeError, TypeError):
        return ServerState.OTHER


def _mutex_name(project_root: Path, port: int) -> str:
    identity = os.path.normcase(str(project_root.resolve())) + ":" + str(port)
    digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:24]
    return "Local\\EstacaoMeteorologicaInicio_" + digest


@contextmanager
def startup_lock(project_root: Path, port: int):
    """Serializa cliques no atalho sem arquivos de lock ou processos a encerrar."""
    if os.name != "nt":
        raise LauncherError("Este atalho foi preparado para Windows.")
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateMutexW.argtypes = [ctypes.c_void_p, wintypes.BOOL, wintypes.LPCWSTR]
    kernel.CreateMutexW.restype = wintypes.HANDLE
    kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel.WaitForSingleObject.restype = wintypes.DWORD
    kernel.ReleaseMutex.argtypes = [wintypes.HANDLE]
    kernel.ReleaseMutex.restype = wintypes.BOOL
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL
    handle = kernel.CreateMutexW(None, False, _mutex_name(project_root, port))
    if not handle:
        raise LauncherError("Nao foi possivel preparar a abertura da estacao. Tente novamente.")
    acquired = False
    try:
        result = kernel.WaitForSingleObject(handle, int((START_TIMEOUT_SECONDS + 10) * 1000))
        if result == 0x102:
            raise LauncherError("A estacao ainda esta sendo iniciada em outra janela. Aguarde e tente novamente.")
        if result not in (0, 0x80):
            raise LauncherError("Nao foi possivel verificar outra abertura da estacao.")
        acquired = True
        yield
    finally:
        if acquired:
            kernel.ReleaseMutex(handle)
        kernel.CloseHandle(handle)


def validate_environment(project_root: Path, *, server_mode: bool = False):
    if not (project_root / "backend" / "main.py").is_file():
        raise LauncherError("A pasta do projeto esta incompleta: backend/main.py nao foi encontrado.")
    if not (project_root / ".env").is_file():
        raise LauncherError("Crie o arquivo .env na raiz do projeto a partir de .env.example antes de iniciar a API.")
    if not server_mode and not (project_root / ".venv" / "Scripts" / "python.exe").is_file():
        raise LauncherError("O Python da .venv nao foi encontrado. Recrie o ambiente virtual do projeto.")
    missing = [name for name in ("uvicorn", "fastapi", "dotenv") if importlib.util.find_spec(name) is None]
    if missing:
        raise LauncherError("Faltam dependencias. Instale requirements.txt usando o Python da .venv do projeto.")


def start_server(project_root: Path, port: int):
    command = [
        str(project_root / ".venv" / "Scripts" / "python.exe"),
        "-u", str(Path(__file__).resolve()), "--servidor",
        "--raiz", str(project_root), "--porta", str(port),
    ]
    try:
        return subprocess.Popen(command, cwd=str(project_root), creationflags=CREATE_NEW_CONSOLE)
    except OSError:
        raise LauncherError("Nao foi possivel abrir o console da API. Confira o ambiente .venv do projeto.") from None


def wait_for_server(process, port: int, timeout: float = START_TIMEOUT_SECONDS):
    deadline = time.monotonic() + timeout
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise LauncherError("A API ainda nao respondeu. Confira a janela Estacao Meteorologica — API e tente novamente.")
        state = probe_server(port, timeout=min(HTTP_TIMEOUT_SECONDS, remaining))
        if state is ServerState.OWN:
            return
        if state is ServerState.OTHER:
            raise LauncherError(f"A porta {port} responde como outro servico. Confira o console; nenhum processo foi encerrado.")
        if process.poll() is not None:
            raise LauncherError("O servidor encerrou antes de ficar pronto. Confira as mensagens no console da API.")
        time.sleep(min(0.25, max(0, deadline - time.monotonic())))


def open_panel(port: int):
    address = origin(port) + "/"
    try:
        opened = webbrowser.open(address, new=2)
    except (OSError, webbrowser.Error):
        opened = False
    if not opened:
        raise LauncherError("A API esta funcionando, mas o navegador nao abriu. Acesse " + address)


def launch_station(project_root: Path = ROOT, port: int = DEFAULT_PORT):
    project_root = Path(project_root).resolve()
    with startup_lock(project_root, port):
        state = probe_server(port)
        if state is ServerState.OWN:
            open_panel(port)
            return
        if state is ServerState.OTHER:
            raise LauncherError(f"Outro servico esta usando a porta {port}. Libere a porta antes de abrir a estacao.")
        if state is ServerState.UNRESPONSIVE:
            raise LauncherError(f"Nao foi possivel confirmar o servico na porta {port}. Confira a API antes de iniciar outra instancia.")
        validate_environment(project_root)
        process = start_server(project_root, port)
        wait_for_server(process, port)
        open_panel(port)


def _console_title(port: int):
    if os.name == "nt":
        try:
            ctypes.windll.kernel32.SetConsoleTitleW(f"Estação Meteorológica — API ({port})")
        except (AttributeError, OSError):
            pass


def run_server(project_root: Path = ROOT, port: int = DEFAULT_PORT) -> int:
    """Executado no console visivel; nao depende do diretorio atual do atalho."""
    project_root = Path(project_root).resolve()
    _console_title(port)
    try:
        validate_environment(project_root, server_mode=True)
        os.chdir(project_root)
        sys.path.insert(0, str(project_root))
        import uvicorn

        print("Estação Meteorológica — API", flush=True)
        print("Painel: " + origin(port) + "/", flush=True)
        print("Mantenha esta janela aberta. Para encerrar, pressione Ctrl+C.", flush=True)
        uvicorn.run("backend.main:app", host="0.0.0.0", port=port,
                    env_file=str(project_root / ".env"), reload=False)
        return 0
    except KeyboardInterrupt:
        return 0
    except (Exception, SystemExit) as error:
        if isinstance(error, SystemExit) and error.code in (0, None):
            return 0
        if isinstance(error, LauncherError):
            print(str(error), flush=True)
        else:
            print("Nao foi possivel iniciar a API. Confira dependencias, .env e disponibilidade da porta.", flush=True)
            print("Tipo do erro: " + type(error).__name__, flush=True)
        try:
            input("Pressione Enter para fechar esta janela...")
        except (EOFError, OSError, KeyboardInterrupt):
            pass
        return 1


def show_error(message: str):
    if os.name == "nt":
        try:
            ctypes.windll.user32.MessageBoxW(None, message, "Estação Meteorológica", 0x10)
            return
        except (AttributeError, OSError):
            pass
    if sys.stderr is not None:
        print(message, file=sys.stderr)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Iniciar a Estacao Meteorologica")
    parser.add_argument("--servidor", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--raiz", type=Path, default=ROOT, help=argparse.SUPPRESS)
    parser.add_argument("--porta", type=int, default=DEFAULT_PORT, help="Porta explicita; padrao 8000")
    arguments = parser.parse_args(argv)
    if not 1 <= arguments.porta <= 65535:
        show_error("A porta deve estar entre 1 e 65535.")
        return 1
    if arguments.servidor:
        return run_server(arguments.raiz, arguments.porta)
    try:
        launch_station(arguments.raiz, arguments.porta)
        return 0
    except LauncherError as error:
        show_error(str(error))
    except Exception:
        show_error("Nao foi possivel abrir a estacao. Confira a pasta do projeto e tente novamente.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
