## Catálogo técnico dos arquivos

Este catálogo descreve o código atual, separando funções executadas na placa, no computador e no navegador. Os nomes são referências para localizar a implementação; não são uma instrução para executar todos os scripts. Configurações privadas e imagens de flash não foram reproduzidas.

### Firmware e coordenação na placa

| Arquivo | Componentes e responsabilidade |
| --- | --- |
| `firmware/main.py` | `main()` cria LDR18, DHT4, MQ34 e BMP SDA21/SCL22. Em laço, lê cada driver, reúne o payload, conecta ao Wi-Fi e chama o cliente HTTP. Trata erros individuais e falhas de envio. |
| `firmware/wifi.py` | `conectar(ssid, senha, timeout=20)` ativa a interface Station e reutiliza ou estabelece conexão. Consulta o estado a cada 250 ms e limita a espera por padrão a 20 s. |
| `firmware/api_client.py` | `enviar(url, chave, dados)` cria POST HTTP/1.0 JSON por socket, envia `X-API-Key`, aceita status 201 e fecha o socket em `finally`. O timeout é 5 s. `DICAS` explica erros 401, 503, 422 e 404. |
| `firmware/config.example.py` | Modelo público de rede, senha, URL, chave, estação e intervalo. Deve ser copiado e preenchido no computador de destino. O arquivo privado `config.py` não integra a entrega pública. |
| `firmware/sensors/__init__.py` | Define o pacote dos drivers. |

A placa usa MicroPython. Copiar esses arquivos para o computador não torna `machine`, `dht` e `network` módulos do Python comum. O backend e o frontend permanecem fora da placa.

### Drivers dos quatro sensores

| Arquivo | Classe/métodos | Resultado e tratamento |
| --- | --- | --- |
| `sensors/ldr.py` | `SensorLDR.__init__()`, `ler()` | Configura entrada digital. Retorna `luz` e `estado`, com 0=Claro e 1=Escuro. |
| `sensors/dht22.py` | `SensorDHT22.__init__()`, `ler()` | Instancia DHT22, respeita 2,5 s entre aquisições, arredonda a uma casa e retorna temperatura/umidade nulas em erro de aquisição. |
| `sensors/mq135.py` | `SensorMQ135.__init__()`, `ler()` | ADC 12 bits, atenuação 11 dB, contagem 0–4095; retorna nulo em falha prevista. |
| `sensors/bmp280.py` | `BMP280.__init__()` | Reseta o dispositivo, espera cópia da NVM, lê 24 bytes de calibração e configura o perfil. |
| `sensors/bmp280.py` | `BMP280._aguardar()` | Verifica status e modo, dormindo entre consultas e respeitando timeout. |
| `sensors/bmp280.py` | `BMP280.ler()` | Dispara conversão, espera, lê RAW, extrai ADCs, calcula temperatura/pressão e valida faixa. |
| `sensors/bmp280.py` | `SensorBMP280.__init__()`, `ler()` | Gerencia SoftI2C, descoberta, instanciação e tentativa posterior de recuperação. Retorna os campos BMP nulos quando não há medição validada. |

No BMP, o barramento é 50 kHz e o timeout de SoftI2C é 5000 µs. A descoberta consulta 0x76/0x77 e espera ID 0x58. O reset escreve 0xB6 em E0; a inicialização usa F5=00 e F4=54; a leitura usa F4=55, perfil forçado T×2/P×16. A espera da conversão é limitada a 1000 ms. O bloco F7–FC contém pressão e temperatura de 20 bits.

O formato de calibração é `<HhhHhhhhhhhh`: T1 e P1 sem sinal; os demais com sinal. O driver rejeita blocos evidentemente vazios/inválidos, ADCs especiais e medidas fora da faixa. O wrapper reinicia a busca quando necessário, sem transformar a exceção em temperatura zero ou pressão inventada.

### API e ciclo de vida

| Componente | Função |
| --- | --- |
| `backend/main.py: impressao_digital()` | Gera os seis primeiros caracteres hexadecimais de SHA-256 para comparar chaves nos logs sem revelar seu conteúdo. |
| `create_app()` | Cria o banco e a aplicação FastAPI, monta arquivos estáticos e registra rotas. Pode receber banco/chave de teste explicitamente. |
| `lifespan()` | Inicializa tabela/índice e registra a condição da chave no início do servidor. |
| `painel()` | Retorna o HTML do frontend. |
| `saude()` | Informa disponibilidade básica da aplicação. |
| `criar()` | Confere chave e persiste um payload validado. |
| `listar()` | Consulta histórico por estação, limite e cursor. |
| `ultima()` | Retorna a última linha ou 404. |
| `backend/__init__.py` | Define o pacote Python. |

A configuração `.env` é carregada a partir da raiz com `override=True`. A aplicação fecha sobre a chave carregada; editar o arquivo sem reiniciar o processo não atualiza essa variável. Consultas são públicas no modelo local; somente o POST exige a chave.

### Modelo e persistência

| Arquivo/componente | Responsabilidade |
| --- | --- |
| `schemas.py: LeituraEntrada` | Tipos, faixas, campos obrigatórios, números finitos e recusa de campos desconhecidos. |
| `LeituraEntrada.validar_estados()` | Coerência Claro/Escuro com0/1 e coerência do booleano BMP com valores presentes/nulos. |
| `LeituraSaida` | Acrescenta `id` e `recebido_em`. |
| `database.py: Banco.__init__()` | Guarda o caminho do arquivo. |
| `Banco.conectar()` | Gerencia a conexão e a transação, com timeout de 10 s. |
| `Banco.inicializar()` | Cria pasta, tabela e índice quando necessário. |
| `Banco.salvar()` | Insere com parâmetros SQL, acrescenta horário UTC e retorna a linha criada. |
| `Banco.listar()` | Combina filtros e retorna linhas por ID decrescente. |

A estrutura possui uma tabela principal `leituras`. A configuração de autenticação não é uma coluna dessa tabela. A exportação SQL anexa descreve a estrutura; a exportação CSV descreve o corte de dados. Nenhuma delas deve substituir o arquivo do banco em execução.

### Frontend

| Arquivo/função | Responsabilidade |
| --- | --- |
| `frontend/index.html` | Estrutura Observatório, seis cartões, status, horário, histórico e exportação. Não possui seletor de estação nem botão Atualizar. |
| `frontend/style.css` | Paleta, tipografia, cartões, tabela e adaptações responsivas. |
| `frontend/app.js: el()` | Localiza elementos por ID. |
| `formatar()` | Formata números em pt-BR e apresenta ausência como travessão. |
| `limpar()` | Redefine dados exibidos e estado da exportação antes de preencher uma resposta válida. |
| `atualizar()` | Consulta a estação fixa `esp32-01`, atualiza cartões e histórico e sinaliza erro/atraso. |
| Evento de exportação | Gera CSV com BOM UTF-8, delimitador `;`, escape de aspas e CRLF. |
| `frontend/favicon.svg` | Mesma rosa dos ventos usada como identidade do atalho. |

A consulta ocorre ao abrir e a cada 5 s, tem timeout de 8 s e evita sobreposição com `ocupado`. A janela é de 100 registros. O status de atraso usa 30 s desde a recepção mais recente. O identificador da estação permanece na consulta e no CSV para manter o vínculo dos dados, mesmo sem um campo editável no painel.

### Iniciador e atalho

| Função/classe de `scripts/iniciar_estacao.py` | Responsabilidade |
| --- | --- |
| `LauncherError`, `ServerState` | Representam erro de operação e os estados própria/desligada/outro serviço/não confirmada. |
| `origin()` | Monta a URL de loopback da porta escolhida explicitamente. |
| `_get_json()` | Faz consulta JSON com limite de tamanho de resposta. |
| `probe_server()` | Confere saúde, título e rotas esperadas, sem usar chave. |
| `_mutex_name()`, `startup_lock()` | Derivam o nome e controlam mutex Win32 por raiz/porta. |
| `validate_environment()` | Verifica arquivos e disponibilidade das dependências de execução. Não revela o conteúdo privado. |
| `start_server()` | Abre `python.exe` da `.venv` em console separado, com argumentos estruturados e diretório explícito. |
| `wait_for_server()` | Aguarda API própria, detecta encerramento e respeita o prazo de partida. |
| `open_panel()` | Abre o navegador e fornece o endereço em caso de falha. |
| `launch_station()` | Coordena reconhecimento, validação, partida e navegador. |
| `_console_title()`, `run_server()` | Executam o modo servidor, com título, Uvicorn e erro visível no console. |
| `show_error()`, `main()` | Diálogo Windows ou stderr e tratamento dos argumentos. |

Os padrões atuais são porta 8000, consulta HTTP 3 s, partida 30 s e espera do mutex 40 s. O atalho usa `pythonw`, enquanto o servidor usa console normal. `--porta` e `--raiz` permitem teste explícito, sem troca automática. Não há encerramento arbitrário de outro serviço.

`scripts/criar_atalho.ps1` valida os arquivos, cria a cópia versionada do ICO, preserva um atalho anterior incompatível e grava destino, argumento, pasta e ícone no Desktop. Usa COM do Windows e libera os objetos ao terminar.

### Diagnóstico, backup e entrega

| Arquivo | Componentes e uso |
| --- | --- |
| `scripts/monitorar_bmp280.py` | `I2CCapturado` e seus métodos registram RAW/calibração; `monitorar()` executa a janela nominal de 90 s, preservando as amostras que o driver calculou e enviando dados reais à API. |
| `scripts/diagnosticar_bmp280.py` | `diagnosticar()` testa linhas, scan, identidade e formas de leitura. Alterna HardwareI2C/SoftI2C e permanece como ferramenta histórica, não a primeira referência de reteste. |
| `scripts/simular.py` | `main()` envia dados fictícios identificados como `simulador`, separados do painel real. |
| `scripts/backup_antes_arduino.py` | `_recusar_link()`, `_percorrer()`, `_fontes()` e `_destino_seguro()` delimitam origem/destino; `_snapshot_sqlite()` e `_metadados_arquivo()` verificam dados; `criar_backup()` e `main()` coordenam a cópia e o manifesto. |
| `scripts/restaurar_flash_esp32.ps1` | `Assert-PlainItem`, `Get-BackupImage` e `Invoke-EsptoolChecked` validam arquivos e executam a restauração manual conferida. Não é uma etapa normal de abrir o painel. |
| `scripts/empacotar.py` | `criar_zip()` produz entrega de código/documentação permitida, valida integridade e evita sobrescrever um arquivo existente. |

O monitor mantém o objeto BMP após `ValueError`, ao contrário do wrapper do programa normal. Esse detalhe deve ser registrado ao comparar janelas. O `api_ok` pode ser verdadeiro mesmo com BMP nulo, porque o payload dos outros sensores foi aceito. `bmp_validas` conta antes do POST. O host precisa resetar a placa depois do monitor.

O backup de manutenção inclui configurações privadas, enquanto a entrega compartilhável as exclui. A imagem da flash é obtida separadamente. A restauração exige validar as duas imagens, o dispositivo e o manifesto; não deve ser disparada só porque um cartão do painel ficou vazio.

### Testes e documentos

| Arquivo | Casos e finalidade |
| --- | --- |
| `tests/test_api.py` | 5 casos de fluxo, persistência, filtros e autenticação. |
| `tests/test_backup_antes_arduino.py` | 11 casos de integridade, snapshots/WAL, destinos e proteção de backups. |
| `tests/test_bmp280.py` | 7 casos incluindo parametrizações de ADC inválido, vetor de compensação, calibração e timeout. |
| `tests/test_empacotar.py` | 2 casos de conteúdo/integridade e recusa de arquivo existente. |
| `tests/test_iniciar_estacao.py` | 21 casos incluindo parâmetros, API própria/alheia, partida, erro, mutex, navegador e Uvicorn. |

Os auxiliares `Relogio`, `Barramento` e as fixtures de isolamento evitam que testes unitários manipulem a placa real ou encerrem o servidor ativo. A contagem é 46, incluindo parametrizações; não é uma contagem de sensores ou de amostras físicas.

`README.md` descreve a estrutura, `COMO_EXECUTAR.md` orienta os integrantes que receberam o ZIP, `ATALHO_WINDOWS.md` explica a operação por clique e `CHANGELOG.md` registra as etapas. Os relatórios BMP preservam evidências de momentos específicos. O relatório completo integra esses materiais, sem apagar suas diferenças históricas.

No código original examinado por AST, foram identificados `BMP280`, `conectar_bmp`, LDR21, DHT4, MQ34 e BMP SCL18/SDA19. Essa verificação não publicou as strings do programa original, que podiam incluir configuração privada. A pinagem de referência hoje é LDR18 e BMP SDA21/SCL22.
