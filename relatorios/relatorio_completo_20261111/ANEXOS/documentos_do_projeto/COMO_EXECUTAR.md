# Estação Meteorológica — projeto completo para o grupo

Extraia o ZIP antes de executar os comandos. Abra a pasta extraida no VS Code
e use o PowerShell nessa pasta. O ambiente virtual, as credenciais e o banco
do notebook original nao acompanham a entrega. O banco e criado automaticamente.

O ZIP inclui o backend FastAPI, painel HTML/CSS/JavaScript, firmware MicroPython,
drivers dos sensores, testes e documentação. Os arquivos `.env.example` e
`firmware/config.example.py` são modelos: cada computador deve configurar sua
rede, endereço do servidor e chave, conforme os passos abaixo. Não é preciso
instalar WinRAR: o Windows também consegue extrair ZIP.

## Servidor e painel no computador

Instale Python 3.10 ou mais recente e execute:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
Copy-Item .env.example .env
```

Edite `.env` e escolha uma API_KEY. Depois:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload --env-file .env
```

Abra http://localhost:8000. Documentacao da API: http://localhost:8000/docs.
Mantenha o terminal aberto. Ctrl+C encerra o servidor. Evite iniciar duas
instancias usando a mesma porta. Alterou a chave? Encerre e inicie novamente.

### Abrir pelo ícone nas próximas vezes

Depois da configuração inicial, crie o atalho na área de trabalho:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\criar_atalho.ps1
```

Nas próximas vezes, dê dois cliques em **Estação Meteorológica**. O atalho
inicia o servidor se necessário e abre o painel. Detalhes sobre energia,
Wi-Fi, encerramento e mudança de pasta: [ATALHO_WINDOWS.md](ATALHO_WINDOWS.md).

## Configurar a placa

O firmware roda em MicroPython no ESP32, separado do Python do computador.
O ESP32 precisa ter MicroPython instalado. Se já executa a estação, preserve
esse firmware; os comandos abaixo enviam os arquivos Python, sem instalar
Arduino nem substituir a imagem completa da flash. Não execute
`firmware/main.py` com o Python do computador: ele importa módulos da placa.
Configure rede e endereco da API em uma copia do modelo:

```powershell
Copy-Item firmware/config.example.py firmware/config.py
ipconfig
.\.venv\Scripts\python.exe -m mpremote connect list
```

Edite o `config.py` com seu SSID, senha, IPv4 do computador e a mesma chave
do `.env`. Mantenha `ESTACAO_ID = "esp32-01"`, identificador mostrado pelo
painel. `API_URL` deve terminar em `/api/leituras`. Exemplo:
`http://192.168.1.100:8000/api/leituras`. Nunca use localhost na placa.
Computador e ESP32 devem estar na mesma rede. O IPv4 pode mudar ao reconectar.

Feche Thonny e monitores seriais. Substitua COM5 pela porta encontrada.
Faça backup dos arquivos existentes antes de enviar uma nova versão.
Os comandos seguintes substituem os arquivos de mesmo nome na placa:

```powershell
.\.venv\Scripts\python.exe -m mpremote connect COM5 fs cp -r firmware/sensors :
.\.venv\Scripts\python.exe -m mpremote connect COM5 fs cp firmware/wifi.py firmware/api_client.py firmware/config.py :
.\.venv\Scripts\python.exe -m mpremote connect COM5 fs cp firmware/main.py :main.py
.\.venv\Scripts\python.exe -m mpremote connect COM5 reset
```

Pinos desta versao: LDR GPIO18, DHT22 GPIO4, MQ-135 GPIO34,
BMP280 SDA GPIO21 e SCL GPIO22. Nos módulos BMP280 de seis pinos usados nos testes,
VCC/CSB vao ao 3V3 e GND/SDO ao GND. Siga os nomes dos pinos,
pois modulos com o pente soldado no outro lado ficam espelhados visualmente.

## Funcionamento confirmado e como conferir sua instalação

Em 11/11/2026, a montagem recuperou as leituras do BMP280 no MicroPython:
foram preservados **217 registros válidos**, entre 14:20:17 e 14:40:03
(UTC−3), com temperatura BMP de 23,4 a 23,7 °C e pressão de 934,86 a
935,12 hPa. Esses valores são uma referência histórica, não valores que
devem ser forçados no código. A causa exata da recuperação não foi comprovada.

O painel mostra diretamente **esp32-01** e atualiza automaticamente a cada
cinco segundos, sem selecionar estação ou clicar em Atualizar. Confira o
horário e os cartões de temperatura/umidade, pressão, luz, gás e temperatura BMP. A
temperatura do DHT22 e a interna do BMP são medidas distintas. Pressão é
exibida em hPa; gás é ADC bruto, não ppm; o LDR fornece Claro/Escuro, não lux.

Uma instalação nova começa com banco vazio. Só aparecerão medidas reais
depois de o ESP32 enviar para esse servidor. O banco será salvo em
`data/estacao.db` e preservado entre reinicializações. Os dados de referência
incluídos em `diagnosticos/referencia_bmp280_20261111/` não são importados
automaticamente nem devem substituir o banco ativo.

Para conferir a recepção sem usar a serial:

```powershell
Invoke-RestMethod 'http://localhost:8000/api/saude'
Invoke-RestMethod 'http://localhost:8000/api/leituras/ultima?estacao_id=esp32-01' |
    Format-List
```

O primeiro comando deve retornar `status: ok`. O segundo retorna 404 enquanto
não houver leitura; depois disso, `id` e `recebido_em` devem avançar. Se o
BMP não tiver medição validada, seus campos ficam nulos e os outros sensores
podem continuar sendo enviados. Se a API recebe dados novos de `esp32-01` e
o painel não atualiza, pressione Ctrl+F5.

O procedimento de reteste de 90 segundos, com captura dos dados brutos e
reset para retomar a estação, está em
[RELATORIO_FUNCIONAMENTO_E_RECUPERACAO_BMP280.md](RELATORIO_FUNCIONAMENTO_E_RECUPERACAO_BMP280.md).
Esse é o guia de referência para uma nova falha. Não é preciso executar
diagnósticos nem instalar firmware Arduino para usar o painel.

## Testes e demonstracao sem placa

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Para dados ficticios, com a API rodando, em outro terminal:

```powershell
$env:API_KEY = "A_MESMA_CHAVE_DO_ENV"
.\.venv\Scripts\python.exe scripts/simular.py
```

Consulte os registros fictícios por
`GET http://localhost:8000/api/leituras?estacao_id=simulador`, abrindo esse
endereço no navegador ou usando a API. O simulador usa o identificador
`simulador`, separado do ESP32. O painel continua mostrando somente
`esp32-01`; os dados fictícios não aparecem nele. Ctrl+C encerra o simulador.

Consulte tambem `README.md` (arquitetura e arquivos) e `CHANGELOG.md` (alteracoes).
