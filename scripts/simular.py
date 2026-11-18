"""Envia dados fictícios para testar o fluxo sem ESP32."""
import json
import os
import random
import time
from urllib.request import Request, urlopen

def main():
    url = os.getenv("API_URL", "http://127.0.0.1:8000/api/leituras")
    chave = os.environ["API_KEY"]
    print("SIMULAÇÃO: estação simulador; Ctrl+C para encerrar")
    while True:
        dados = dict(estacao_id="simulador", luz=0, estado="Claro",
                     temperatura=round(random.uniform(22, 28), 1), umidade=60,
                     gas=1200, pressao=1013.2, temperatura_bmp=25, bmp_conectado=True)
        pedido = Request(url, data=json.dumps(dados).encode(),
                         headers={"Content-Type":"application/json", "X-API-Key":chave}, method="POST")
        try:
            with urlopen(pedido, timeout=5) as resposta:
                print(resposta.status, resposta.read().decode())
        except OSError as erro:
            print("Falha no envio:", erro)
        time.sleep(5)

if __name__ == "__main__":
    main()
