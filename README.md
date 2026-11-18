# Estação meteorológica com ESP32

Pasta atual neste notebook: `C:\Users\Windows\computer-science\estacao-meteorologica`. O atalho da área de trabalho usa esta instalação.

Projeto reorganizado a partir do arquivo `main.py.py` fornecido. O original foi mantido em `backup_esp32/main_original_esp32.py`. O firmware continua em **MicroPython**; o FastAPI roda em **Python no computador**, e o navegador exibe o painel. O VS Code é o editor dos dois ambientes.

```text
ESP32 / sensores → Wi-Fi / POST JSON → FastAPI → SQLite em disco
                                         ↓
                                Painel HTML/CSS/JS
```

O ESP32 coleta e envia independentemente do navegador. O servidor precisa estar ligado para receber e persistir as leituras. O painel mostra diretamente a estação `esp32-01` e consulta o banco automaticamente a cada cinco segundos, sem seleção de estação ou botão Atualizar. Mostra falhas como valores ausentes, alerta para leituras com mais de 30 segundos e exporta os últimos 100 registros em CSV.

> Abrir pelo ícone **Estação Meteorológica** na área de trabalho: [ATALHO_WINDOWS.md](ATALHO_WINDOWS.md). O atalho inicia o servidor quando necessário e abre o painel; o ESP32 pode permanecer alimentado pela fonte e enviar por Wi-Fi.

> Histórico detalhado de correções: [CHANGELOG.md](CHANGELOG.md).

> Gravação da apresentação: [ROTEIRO_GRAVACAO.md](ROTEIRO_GRAVACAO.md), com os blocos de 2:30 a 7:00 adaptados ao envio HTTP, ao SQLite e ao painel atual. Para acompanhar inserções reais, execute `.\.venv\Scripts\python.exe -u scripts\acompanhar_banco.py`; a consulta é somente leitura. Os logs novos de Wi-Fi, sensores e payload JSON em `firmware/main.py` só aparecem na placa depois de transferir o arquivo atualizado e reiniciar o ESP32.

> Testes e pinagem atual do BMP280: [DIAGNOSTICO_BMP280.md](DIAGNOSTICO_BMP280.md).

> Funcionamento recuperado, evidências e procedimento se voltar a falhar: [RELATORIO_FUNCIONAMENTO_E_RECUPERACAO_BMP280.md](RELATORIO_FUNCIONAMENTO_E_RECUPERACAO_BMP280.md).

> Relatório técnico do módulo do professor: [RELATORIO_BMP280_PROFESSOR.md](RELATORIO_BMP280_PROFESSOR.md).

> Comparação com Arduino/Adafruit e restauração verificada: [TESTE_ARDUINO_BMP280.md](TESTE_ARDUINO_BMP280.md).

> Recebeu o projeto por ZIP? Comece por [COMO_EXECUTAR.md](COMO_EXECUTAR.md).

## 1. Executar no VS Code / Windows

Abra esta pasta no VS Code. Instale Python 3.10+ e a extensão Python da Microsoft. No terminal PowerShell, na raiz do projeto:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
Copy-Item .env.example .env        # depois edite API_KEY
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

> **Não copie a pasta `.venv` entre computadores.** Ela guarda o caminho absoluto do Python que a criou e deixa de funcionar em outra máquina (erro `did not find executable ...`). Em outro computador, apague-a e recrie com os comandos acima.

**A chave vem do arquivo `.env`.** O backend o lê ao iniciar e ele tem prioridade sobre qualquer variável `$env:API_KEY` já definida no terminal, para que exista uma única fonte da verdade. Use a mesma chave em `firmware/config.py`. Alterou o `.env`? **Encerre o Uvicorn por completo e inicie de novo**: o `--reload` só recarrega ao mudar arquivos `.py`, e uma chave já carregada na memória não muda sozinha.

Ao iniciar, o servidor registra no log `API_KEY carregada (impressao digital xxxxxx)`. A impressão digital identifica a chave sem revelá-la; veja a seção 7 para usá-la no diagnóstico.

Abra **http://localhost:8000** para o painel e **http://localhost:8000/docs** para a documentação interativa da API. Nunca use `http://0.0.0.0:8000` no navegador: esse endereço só serve para o servidor escutar todas as interfaces. O painel começa vazio; não há dados fictícios misturados automaticamente aos reais.

Selecione `.venv/Scripts/python.exe` em **Python: Select Interpreter**. Para depurar com F5, escolha **FastAPI — estação**; a configuração também lê o `.env`.

SQLite não exige instalar um servidor de banco. Os dados ficam em `data/estacao.db`, criado na inicialização, e continuam disponíveis ao reiniciar a API. Opcionalmente defina `$env:DATABASE_PATH` com outro caminho. Para backup simples, pare a API e copie o arquivo do banco. Não apague `data/` para atualizar o código.

> **Atenção com OneDrive:** se o projeto estiver numa pasta sincronizada, o OneDrive pode travar ou corromper o arquivo SQLite durante a gravação. Prefira apontar `DATABASE_PATH` para uma pasta fora do OneDrive (por exemplo `C:\dados\estacao.db`) ou pausar a sincronização durante o uso.

## 2. Preparar o ESP32

A placa que já funciona pelo Thonny provavelmente já tem MicroPython. Não é necessário reinstalá-lo para trocar de editor. Feche Thonny e qualquer monitor serial antes de usar `mpremote`, pois a porta não pode ser usada simultaneamente.

Pinos atuais para o ESP32 clássico:

| Sensor | Ligação de sinal | Valor |
| --- | --- | --- |
| LDR com saída digital | GPIO18 | 0 = claro, 1 = escuro |
| DHT22 | GPIO4 | °C e umidade relativa % |
| MQ-135 | GPIO34 / ADC | inteiro bruto 0–4095 |
| BMP280 | SCL GPIO22, SDA GPIO21 | °C e pressão hPa |

Use GND comum. Confira alimentação e nível de sinal do módulo utilizado: entradas do ESP32 são de 3,3 V; a saída analógica de módulos MQ alimentados em 5 V pode exigir divisor de tensão. O LDR do código é digital, não fornece lux. MQ-135 não fornece ppm ou índice de qualidade do ar sem aquecimento, calibração e modelo próprios. O driver BMP280 reconhece ID `0x58` nos endereços `0x76` e `0x77`; BME280 (ID `0x60`) não é compatível com este driver.

Descubra o IPv4 do computador com `ipconfig`. Conecte computador e placa à mesma rede local, sem isolamento entre clientes; para ESP32 clássico, utilize Wi-Fi de 2,4 GHz. Permita a porta TCP 8000 no firewall da rede privada se necessário. `localhost` no ESP32 aponta para a própria placa; em `API_URL` use o IPv4 do computador. **Em hotspot de celular o IP muda ao reconectar**: confira `ipconfig` e atualize `API_URL` sempre que o painel parar de receber dados.

```powershell
Copy-Item firmware/config.example.py firmware/config.py
.\.venv\Scripts\mpremote.exe connect list
```

Edite `firmware/config.py`: `WIFI_SSID`, `WIFI_PASSWORD`, `API_URL`, `API_KEY` e `INTERVALO_SEGUNDOS`. Mantenha `ESTACAO_ID = "esp32-01"`, identificador exibido pelo painel. Exemplo de URL: `http://192.168.1.100:8000/api/leituras`. Não use quebras de linha na chave ou URL. O intervalo padrão é cinco segundos, com mínimo de três no firmware. A chave e a senha não são versionadas.

Substitua `COM3` pela porta real (ela muda; confira com `connect list`). Faça backup dos arquivos atuais da placa antes de substituí-los. Da raiz do projeto:

```powershell
.\.venv\Scripts\mpremote.exe connect COM3 fs cp -r firmware/sensors :
.\.venv\Scripts\mpremote.exe connect COM3 fs cp firmware/wifi.py firmware/api_client.py firmware/config.py :
.\.venv\Scripts\mpremote.exe connect COM3 fs cp firmware/main.py :main.py
.\.venv\Scripts\mpremote.exe connect COM3 reset
.\.venv\Scripts\mpremote.exe connect COM3 repl
```

Os arquivos devem ficar na raiz da placa, com a pasta `sensors/` ao lado de `main.py`. `main.py` inicia automaticamente ao reiniciar. Ctrl+C no REPL interrompe o laço para manutenção. Não execute `firmware/main.py` pelo Python do computador: `machine`, `network` e `dht` pertencem ao MicroPython. Não envie `backend/`, `frontend/` ou `.venv/` à placa. Se usar outro modelo de ESP32, revise os pinos e a API ADC correspondente.

**Toda alteração em `config.py`, `api_client.py` ou `main.py` só vale depois de copiada para a placa e de um `reset`.** Editar o arquivo no computador não muda o que a placa executa.

## 3. Testar sem hardware

Com a API rodando, abra outro terminal na raiz:

```powershell
$env:API_KEY = (Get-Content .env | Where-Object { $_ -like 'API_KEY=*' }) -replace '^API_KEY=',''
.\.venv\Scripts\python.exe scripts/simular.py
```

Consulte os registros fictícios por `GET http://localhost:8000/api/leituras?estacao_id=simulador`, abrindo esse endereço no navegador ou usando a API. Eles ficam separados pelo identificador `simulador`; o painel continua mostrando somente `esp32-01`. Ctrl+C encerra o simulador.

Testes automatizados:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Os testes usam banco temporário e verificam autenticação (inclusive chave errada sem gravação), validação (inclusive payload parcial), valores nulos em falhas, filtros, paginação, arquivos do painel, preservação dos registros após recriar a aplicação e a impressão digital da chave. Também verificam o driver BMP280, os backups e o empacotamento para entrega. Não dependem de hardware; o comando acima apresenta o resultado da versão recebida.

## 4. Estrutura e funções

| Arquivo | Responsabilidade e funções |
| --- | --- |
| `firmware/main.py` | `main()` instancia sensores, chama `ler()` de cada um (uma falha inesperada em um driver é registrada e não interrompe os demais), reúne dados, conecta e envia em laço; trata falhas de comunicação. |
| `firmware/config.example.py` | Modelo de configuração com valores de exemplo; copie para `config.py`, que contém os valores locais. |
| `firmware/wifi.py` | `conectar(ssid, senha, timeout)` reutiliza conexão ou tenta conectar, com espera limitada a 20 segundos. |
| `firmware/api_client.py` | `enviar(url, chave, dados)` faz POST HTTP por socket, aplica timeout de cinco segundos, exige status 201 e fecha a conexão. Em recusa, a mensagem inclui o código HTTP e a causa provável (`DICAS`: 401, 503, 422, 404). Resolução DNS depende da pilha da placa; prefira IPv4 local. |
| `firmware/sensors/__init__.py` | Declara o pacote de sensores. |
| `firmware/sensors/ldr.py` | `SensorLDR.__init__()` configura GPIO; `ler()` retorna `luz` e `estado`. |
| `firmware/sensors/dht22.py` | `SensorDHT22.__init__()` configura DHT22; `ler()` respeita intervalo mínimo de 2,5 s e retorna temperatura/umidade ou nulos em falha. |
| `firmware/sensors/mq135.py` | `SensorMQ135.__init__()` configura ADC de 12 bits; `ler()` retorna leitura bruta ou nulo. |
| `firmware/sensors/bmp280.py` | `BMP280.__init__()` lê calibração e configura sensor; `BMP280.ler()` compensa temperatura e pressão com o algoritmo original. `SensorBMP280.ler()` descobre endereço/ID, faz a leitura e tenta redetectar sensor ausente a cada cinco segundos. |
| `backend/__init__.py` | Declara pacote da API. |
| `backend/main.py` | Carrega o `.env` (com prioridade). `impressao_digital()` gera identificador curto da chave para logs. `create_app()` configura aplicação, banco, rotas e frontend; `lifespan()` inicializa o banco e registra se a chave foi carregada. `painel()`, `saude()`, `criar()`, `listar()` e `ultima()` atendem as rotas abaixo; `criar()` registra no log a impressão digital da chave rejeitada. `app` é o objeto servido pelo Uvicorn. |
| `backend/schemas.py` | `LeituraEntrada` define tipos, limites e campos permitidos; `validar_estados()` verifica coerência de LDR/BMP280. `LeituraSaida` acrescenta ID e horário. |
| `backend/database.py` | `Banco.conectar()` gerencia conexão e transação; `inicializar()` cria tabela/índice; `salvar()` insere valores com parâmetros SQL; `listar()` consulta por estação, limite e cursor. |
| `frontend/index.html` | Estrutura acessível do painel de `esp32-01`, cartões e histórico. |
| `frontend/style.css` | Aparência e adaptação para celular, tablet e desktop. |
| `frontend/app.js` | `formatar()` apresenta valores; `limpar()` redefine painel; `atualizar()` consulta a API para `esp32-01` a cada cinco segundos, sinaliza atraso/falha e preenche o histórico. O botão de exportação gera CSV. |
| `scripts/iniciar_estacao.py` | Inicia a estação pelo atalho, reconhece a API já ativa, abre o navegador e inicia um console do servidor quando necessário. |
| `scripts/criar_atalho.ps1` | Cria o atalho Windows para a pasta atual, com ícone próprio. |
| `assets/estacao-meteorologica.svg` / `.ico` / `.png` | Vetor original, ícone do Windows em vários tamanhos e prévia do desenho. |
| `scripts/simular.py` | `main()` gera e envia leituras fictícias para a estação `simulador`. |
| `scripts/backup_antes_arduino.py` | `criar_backup()` preserva fontes e configurações privadas, cria snapshot consistente do SQLite e registra hashes em um destino novo; a imagem da flash é obtida separadamente. |
| `scripts/restaurar_flash_esp32.ps1` | Valida duas imagens completas, SHA-256 e identidade da placa; restaura a flash, verifica a gravação e reinicia somente após sucesso. Uso restrito ao ESP32 clássico de 4 MB e às condições descritas no manifesto. |
| `diagnosticos/arduino_bmp280/` | Sketch C++ temporário com a biblioteca Adafruit original; `setup()` inicializa serial/I²C e `loop()` registra bytes brutos e resultados. A estação normal volta a executar após restaurar o MicroPython. |
| `tests/test_api.py` | Cobre fluxo/persistência/filtros, ausência de chave, chave errada, impressão digital e payload parcial. |
| `requirements.txt` | Dependências do servidor. |
| `requirements-dev.txt` | Acrescenta ferramentas de teste e comunicação serial. |
| `.vscode/launch.json` | Configuração para depurar o backend pelo F5. |
| `.vscode/extensions.json` | Recomenda extensões Python/Pylance. |
| `.env.example` | Modelo da chave de API. |
| `.gitignore` | Exclui credenciais, ambiente virtual, banco, caches, ferramentas `.tools/` e backups privados do versionamento. |
| `backup_esp32/` | Originais do Thonny, cópias da placa, imagens integrais da flash e snapshots do banco. **Contém configurações privadas e senhas**; não compartilhe. |
| `README.md` / `CHANGELOG.md` | Instalação, arquitetura, diagnóstico e histórico de alterações. |

## 5. Contrato da API e banco

| Método / rota | Uso |
| --- | --- |
| `GET /` | Painel web. |
| `GET /api/saude` | Verifica se a aplicação responde. |
| `POST /api/leituras` | Valida e salva leitura; exige cabeçalho `X-API-Key`; retorna 201. |
| `GET /api/leituras?estacao_id=esp32-01&limite=100` | Histórico em ordem decrescente de ID. Limite de 1 a 1000. Sem estação, retorna todas. |
| `GET /api/leituras?antes_id=123` | Página de registros anteriores ao ID informado; pode combinar filtros. |
| `GET /api/leituras/ultima?estacao_id=esp32-01` | Última leitura ou 404 quando não há registros. |
| `GET /docs` | Documentação interativa com schemas completos. |

Exemplo de corpo enviado pelo ESP32:

```json
{"estacao_id":"esp32-01","luz":0,"estado":"Claro","temperatura":25.5,"umidade":60,"gas":1200,"pressao":1013.2,"temperatura_bmp":25,"bmp_conectado":true}
```

DHT22 com falha envia `temperatura` e `umidade` nulos. BMP280 ausente envia `pressao` e `temperatura_bmp` nulos e `bmp_conectado=false`. Leituras fora dos limites são rejeitadas com 422; chave incorreta retorna 401; servidor sem chave configurada retorna 503 para gravação. `luz`, `estado` e `bmp_conectado` são obrigatórios: se o driver do LDR ou do BMP280 falhar de forma inesperada, o payload sai incompleto e a leitura é rejeitada com 422 (e registrada no console da placa).

A tabela `leituras` contém todos os campos do corpo, `id` inteiro incremental e `recebido_em` em UTC ISO 8601, atribuído pelo servidor na recepção. Esse horário **não é o instante exato de aquisição na placa**. O navegador converte para seu horário local. Valores ausentes ficam como SQL NULL, nunca como zero fictício. O booleano BMP é armazenado como inteiro SQLite e retornado como booleano pela API.

## 6. Limitações e próximos passos

Implementação para rede local de laboratório. HTTP e chave compartilhada protegem apenas a gravação por uma verificação simples; consultas são públicas para dispositivos com acesso à API. Para exposição na internet, adicione HTTPS e controle de acesso apropriado.

Há reconexão Wi-Fi e nova tentativa nos ciclos seguintes, mas **não há fila offline**: se o servidor estiver desligado ou o envio falhar, aquela amostra não será reenviada. Os registros já confirmados pelo servidor permanecem no banco. O intervalo entre aquisições inclui o tempo gasto em conexão/envio. Não há deduplicação para resultados de envio ambíguos nem política de remoção automática do histórico. Erros de inicialização de hardware podem exigir reinício/correção da ligação.

O limite de 30 s do alerta "Sem leituras recentes" do painel é fixo em `frontend/app.js`; se `INTERVALO_SEGUNDOS` for aumentado perto desse valor, o alerta aparecerá indevidamente.

A validação física do ESP32, alimentação, calibração, conexão serial e comunicação na rede deve ser realizada com a placa. Os testes de software não substituem essa etapa. A interface deve ser conferida visualmente no navegador.

## 7. Diagnóstico: o painel não recebe dados

Siga a ordem; cada passo isola uma causa diferente.

| Sintoma | Causa provável | Como confirmar / corrigir |
| --- | --- | --- |
| Painel não abre, ou mostra outra aplicação | Porta 8000 ocupada por outro programa (`WinError 10048/10013`) | `netstat -ano \| Select-String ':8000'` e `Get-CimInstance Win32_Process -Filter "ProcessId=<PID>"`. Encerre o outro programa ou use outra porta **e** atualize a porta em `API_URL` do ESP32. |
| `/api/saude` não devolve `{"status":"ok"}` | O FastAPI da estação não está rodando (ou outro serviço respondeu) | Inicie com o comando da seção 1 e olhe o terminal. |
| ESP32 imprime `Tempo de conexao Wi-Fi esgotado` | SSID/senha errados ou rede 5 GHz | Confira `config.py` e use 2,4 GHz. |
| ESP32 imprime erro de conexão/timeout, nenhum POST no log do servidor | **IP errado** (hotspot mudou), firewall ou computador em outra rede | `ipconfig`; atualize `API_URL`; copie `config.py` e reinicie a placa; libere a porta 8000 no firewall privado. |
| Log do servidor: `POST ... 503` | `.env` vazio ou sem `API_KEY` | O startup mostra `API_KEY ausente`. Preencha o `.env` e reinicie o Uvicorn. |
| Log do servidor: `POST ... 401` | Chave diferente ou chave antiga na memória | O log mostra `Chave rejeitada: recebida=A esperada=B`. Se **B** não bate com `impressao digital` do `.env` atual, o processo é antigo: reinicie. Se bate, a chave da placa é outra: reenvie `config.py` e dê `reset`. |
| Log do servidor: `POST ... 422` | Payload inválido (campo fora do limite ou sensor com falha total) | O corpo da resposta diz o campo; veja também `/docs`. |
| Placa executa comportamento antigo | Firmware antigo ainda na placa (o `main.py` do Thonny) | Copie todos os arquivos da seção 2 e dê `reset`. |
| Painel mostra `—` em pressão e BMP | BMP280 ausente ou medição inválida | Confira SDA GPIO21, SCL GPIO22, alimentação 3,3 V, endereço `0x76/0x77` e ID `0x58`. Veja os registros brutos e [DIAGNOSTICO_BMP280.md](DIAGNOSTICO_BMP280.md). |
| Painel mostra `API indisponível` | Navegador sem acesso ao servidor | Teste `http://localhost:8000/api/saude` no mesmo navegador. |
| `mpremote`: porta em uso | Thonny, REPL ou outro monitor serial aberto | Feche-os. A porta COM pode mudar: `mpremote connect list`. |

Para obter a impressão digital da chave do firmware sem exibi-la (compare com a do log do servidor):

```powershell
.\.venv\Scripts\python.exe -c "import re,hashlib;k=re.search(r'API_KEY\s*=\s*[\"\'](.*)[\"\']',open('firmware/config.py',encoding='utf-8').read()).group(1);print(hashlib.sha256(k.encode()).hexdigest()[:6])"
```

Referências oficiais consultadas: [FastAPI: arquivos estáticos](https://github.com/fastapi/fastapi/blob/master/docs/en/docs/tutorial/static-files.md), [MicroPython: ESP32](https://www.micropython.org/resources/docs/en/latest/esp32/quickref.html) e [mpremote](https://docs.micropython.org/en/latest/reference/mpremote.html).
