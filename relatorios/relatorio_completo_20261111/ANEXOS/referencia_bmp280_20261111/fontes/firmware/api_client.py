import socket
import ujson

DICAS = {
    b"401": "API_KEY do config.py difere da do servidor, ou o servidor ainda usa chave antiga (reinicie-o)",
    b"503": "servidor sem API_KEY configurada (.env vazio ou nao carregado)",
    b"422": "JSON rejeitado pela validacao (veja o terminal do servidor)",
    b"404": "caminho da API_URL incorreto (esperado /api/leituras)",
}

# HTTP local com timeout explicito, sem dependencias extras no ESP32.
def enviar(url, chave, dados):
    if not url.startswith("http://"):
        raise ValueError("Use uma URL http:// da rede local")
    destino = url[7:].split("/", 1)
    host_porta = destino[0].split(":", 1)
    host = host_porta[0]
    porta = int(host_porta[1]) if len(host_porta) == 2 else 80
    caminho = "/" + destino[1] if len(destino) == 2 else "/"
    corpo = ujson.dumps(dados).encode()
    cabecalho = ("POST " + caminho + " HTTP/1.0\r\nHost: " + destino[0] +
                 "\r\nContent-Type: application/json\r\nX-API-Key: " + chave +
                 "\r\nContent-Length: " + str(len(corpo)) + "\r\nConnection: close\r\n\r\n").encode()
    conexao = socket.socket()
    conexao.settimeout(5)
    try:
        conexao.connect(socket.getaddrinfo(host, porta)[0][-1])
        conexao.sendall(cabecalho)
        conexao.sendall(corpo)
        resposta = b""
        while b"\r\n" not in resposta and len(resposta) < 256:
            parte = conexao.recv(64)
            if not parte:
                break
            resposta += parte
        status = resposta.split(b" ", 2)
        codigo = status[1] if len(status) >= 2 else b"?"
        if codigo != b"201":
            # A dica separa causas diferentes que, no log cru, parecem todas "falhou".
            dica = DICAS.get(codigo, "resposta inesperada (outro programa na porta?)")
            raise OSError("API recusou leitura (HTTP " + codigo.decode() + "): " + dica)
    finally:
        conexao.close()
