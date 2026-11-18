# BMP280 — referência de funcionamento e recuperação da estação

**Data:** 11 de novembro de 2026.  
**Fuso:** America/Sao_Paulo, UTC−3.  
**Projeto observado:** `C:\Users\Windows\Desktop\projeto-cc-v2\projeto-cc`.  
**Corte da exportação:** 14:40:09; último registro incluído recebido às 14:40:03.  
**Pasta atual após a mudança de local:** `C:\Users\Windows\computer-science\estacao-meteorologica`. O caminho observado acima foi preservado como contexto histórico; o comando de reteste abaixo usa a pasta atual.

**Objetivo:** guardar uma referência verificável da montagem funcionando e orientar o diagnóstico se as leituras voltarem a falhar.

## 1. Resultado comprovado e limite da conclusão

A estação voltou a receber temperatura interna e pressão compensada do BMP280. Entre **14:20:17 e 14:40:03**, o banco contém **217 registros da estação `esp32-01`, todos com os dois campos BMP preenchidos**, IDs **3443 a 3659**. São **19 minutos e 46 segundos**, sem registro BMP inválido nessa janela. Isso comprova funcionamento durante o período observado, sem garantir estabilidade permanente ou precisão metrológica.

| Indicador da janela exportada | Resultado |
| --- | --- |
| Temperatura BMP mínima/máxima | 23,4 / 23,7 °C |
| Pressão mínima/máxima | 934,86 / 935,12 hPa |
| Registros BMP válidos / não validados | 217 / 0 |
| Intervalo mediano entre recepções | 5,518 s |
| Maior intervalo | 9,156 s, entre IDs 3463 e 3464 |
| Última medição BMP da exportação | 23,4 °C e 935,00 hPa, ID 3659 |
| Outros sensores no ID 3659 | DHT22: 22,9 °C / 76,6%; MQ-135: ADC 393; LDR: 0 / Claro |

O intervalo maior coincide com a passagem do monitor temporário para o programa normal após reset. Essa coincidência temporal não é uma medição da duração exata do boot.

**Não descobrimos uma causa única comprovada para a recuperação.** Houve orientação de troca de módulo e manipulação física antes do novo teste. Os registros válidos **3443, 3444 e 3445 já estavam chegando pelo programa normal antes do monitor iniciado por volta de 14h20min31s**. Portanto, o monitor de diagnóstico não foi necessário para iniciar essa recuperação. Nenhum novo firmware, atualização de driver, compensação artificial ou nova biblioteca foi instalado no teste que deu certo.

## 2. Qual módulo funcionou: como interpretar a identificação

O usuário foi orientado a substituir o HW-611 pelo segundo módulo e respondeu **“pode ir”**. O teste foi executado nesse contexto. Não houve inspeção visual remota da troca nem leitura de número de série individual. A denominação **“segundo módulo” é contextual**, e o relatório preserva essa limitação.

No teste válido, o bloco de calibração foi diferente do bloco registrado anteriormente no módulo identificado como HW-611 do professor. Essa diferença fornece uma referência concreta para comparações futuras. **Ela não substitui uma etiqueta física e não identifica retroativamente o módulo dos registros antigos.**

O banco guarda `estacao_id=esp32-01`, que identifica a estação configurada. Não guarda fotografia, etiqueta do BMP, calibração, RAW ou sessão de troca. `0x58` é o ID de tipo de chip; `0x76` é o endereço selecionado pela ligação de SDO. Esses dois valores são compartilháveis entre módulos. [Bosch, ID e interface I²C](https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bmp280-ds001.pdf#page=24).

Para futuras trocas, marcar fisicamente os três módulos como **1 / professor**, **2** e **3**, fotografar os nomes dos terminais e anotar a hora da troca. O nome da placa HW-611 ou GY-BME/P280 não certifica sozinho o fabricante efetivo do chip.

## 3. Montagem de referência

Esta é a ligação informada durante os testes. As consultas digitais confirmam comunicação, mas não certificam tensão real, solda, posição dos resistores ou continuidade de cada contato.

| Terminal escrito no BMP | Ligação de referência |
| --- | --- |
| VCC | 3V3 do ESP32 |
| GND | GND do ESP32 |
| SDA / SDI | D21 / GPIO21 |
| SCL / SCK | D22 / GPIO22 |
| CSB / CS | 3V3 para operação I²C |
| SDO | GND para endereço `0x76` |

**Seguir o nome impresso do terminal**, especialmente ao trocar placas com os pinos soldados por faces opostas. Não usar a posição esquerda/direita de outro módulo como referência. Desligar a USB e qualquer outra alimentação antes de mudar fios. Os demais sensores podem continuar montados.

| Outro sensor | Sinal no ESP32 | Campo da API |
| --- | --- | --- |
| DHT22, sensor de temperatura/umidade | GPIO4 | `temperatura`, `umidade` |
| LDR com saída digital | GPIO18 | `luz`, `estado` |
| MQ-135 | GPIO34 / ADC | `gas` |

**GPIO18 pertence ao LDR nesta montagem.** O DHT22 não foi transferido para D18. A ligação SDA22/SCL21 foi uma inversão temporária posteriormente desfeita; não é a configuração de referência.

O usuário informou dois resistores de **4,7 kΩ**. Não houve medição da resistência equivalente nem verificação instrumental da posição final. Antes de acrescentar outros, conferir os pull-ups já existentes no módulo e na protoboard: colocá-los em paralelo reduz a resistência equivalente. O dimensionamento depende do barramento, frequência e capacitância. [Espressif, introdução ao I²C](https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-reference/peripherals/i2c.html#introduction).

Uma interrupção em CSB pode ter consequências diferentes de um simples erro de endereço: a Bosch documenta seleção de SPI por CSB baixo, com retorno ao I²C somente após power-on-reset. Isso é uma possibilidade a verificar se ele deixar de responder, **não um evento demonstrado nesta recuperação**. [Bosch, seleção de interface](https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bmp280-ds001.pdf#page=27).

## 4. Programa e parâmetros que estavam funcionando

O firmware é **MicroPython**. FastAPI, SQLite e o navegador rodam no computador. O teste Arduino anterior foi encerrado e a imagem original da placa foi restaurada e verificada. A recuperação atual ocorreu depois disso, no MicroPython.

| Item | Referência observada |
| --- | --- |
| Placa / porta usada nos testes | ESP32 clássico / COM5 |
| Runtime observado anteriormente nesta sessão | MicroPython 1.29.0, Generic ESP32 |
| Ferramenta do computador | `mpremote 1.29.0`, via Python da `.venv` |
| Transporte do BMP | `SoftI2C`, SDA21, SCL22, 50.000 Hz |
| Timeout do SoftI2C | 5.000 µs; não é o tempo total de uma medição |
| Endereço / ID no teste válido | `0x76` / `0x58` — 88 em JSON decimal |
| Reset do BMP pelo driver | escrita `0xB6` em `0xE0`, espera e consulta de status |
| Configuração inicial | `0xF5=0x00`, `0xF4=0x54` |
| Aquisição em `ler()` | `0xF4=0x55`, conversão forçada, T×2 e P×16 |
| Espera da conversão | até 1.000 ms, verificando status e retorno ao modo sleep |
| Bloco bruto consumido pelo cálculo | seis bytes a partir de `0xF7` |
| Intervalo configurado no teste | 5 s; no programa normal soma-se o tempo de aquisição/envio |
| Filtro IIR do perfil atual | desligado, `0xF5=0x00` |

Os parâmetros acima descrevem o fonte e os registros observados; não são uma alegação de configuração universal para toda placa vendida como “280”.

O monitor registrou `cfg_f3_f5="045400"` depois da aquisição. São os bytes F3, F4 e F5 nessa ordem. F4=`0x54` é o estado observado após a conversão forçada; não significa que o comando `0x55` não foi enviado. F3=`0x04` também fica preservado na evidência: seu bit 2 não é um dos dois indicadores definidos no datasheet. O driver consulta os bits 0 e 3. Essa observação não foi usada para concluir causa de falha ou autenticidade do chip.

## 5. Evidência bruta da medição válida

No monitor de aproximadamente 90 segundos houve **18 tentativas, 18 medições BMP válidas e 18 envios aceitos pela API**, com uma única inicialização. O proxy `I2CCapturado` registrou **o mesmo bloco de seis bytes utilizado pelo cálculo daquela chamada `ler()`**. Consultas posteriores de calibração e ID não sobrescreveram esse RAW.

| Informação | Primeiro registro do monitor válido |
| --- | --- |
| RAW completo, pressão seguida de temperatura | `6028507f2480` |
| Três bytes da pressão | `60 28 50` |
| Três bytes da temperatura | `7f 24 80` |
| ADC de pressão, 20 bits | 393861 |
| ADC de temperatura, 20 bits | 520776 |
| Temperatura calculada independentemente | 23,58981788696 °C |
| Pressão calculada independentemente | 935,01291463091 hPa |
| Valores arredondados enviados | 23,6 °C e 935,01 hPa |

Último RAW do monitor: `6021e07f1080`. Na janela, ADC_T variou entre **520456 e 520776**, e ADC_P entre **393756 e 393861**. Os resultados ficaram em **23,5–23,6 °C** e **935,00–935,09 hPa**. Houve coerência entre calibração fresca, cache, RAW e cálculo, sem erro registrado nas 18 tentativas.

O bloco de calibração de 24 bytes foi:

```text
266d276918fc7d9520d6d00b9f130e01f9ff8c3cf8c67017
```

Comparação dos coeficientes decodificados:

| Coeficiente | Referência com leitura válida às 14h20 | Referência anterior do HW-611 |
| --- | ---: | ---: |
| T1 | 27942 | 27348 |
| T2 | 26919 | 25466 |
| T3 | −1000 | 50 |
| P1 | 38269 | 38073 |
| P2 | −10720 | −10642 |
| P3 | 3024 | 3024 |
| P4 | 5023 | 5077 |
| P5 | 270 | −7 |
| P6 | −7 | −7 |
| P7 | 15500 | 15500 |
| P8 | −14600 | −14600 |
| P9 | 6000 | 6000 |

A referência anterior era `d46a7a633200b9946ed6d00bd513f9fff9ff8c3cf8c67017`. Esses bytes foram **lidos**, não inventados nem ajustados. Cada módulo deve ser calculado com os próprios coeficientes lidos; não copiar os valores desta tabela para outro sensor. A calibração de fábrica não é uma configuração para editar manualmente. [Bosch, compensação e parâmetros de fábrica](https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bmp280-ds001.pdf#page=21).

## 6. Comparação com o estado que falhava

| Teste | Módulo conforme identificação disponível | Resultado |
| --- | --- | --- |
| 11h46–11h47, IDs 2334–2346 | Segundo, conforme confirmação naquele período | 13 registros plausíveis, depois perdeu continuidade |
| 12h15–12h19, IDs 2617–2660 | Atribuído ao professor na ocasião; identidade posteriormente questionada | 44 registros plausíveis; sem RAW/calibração associados no banco |
| Arduino, início 12h56 | HW-611 do professor conforme identificação do usuário | 179 amostras, ADC térmico zero em todas, nenhuma medição válida |
| MicroPython, monitor 13h37 | Contexto do módulo anteriormente conectado | 18 amostras com ADC térmico zero |
| MicroPython, monitor 14h16 | HW-611 confirmado explicitamente durante o teste | 18 amostras com ADC térmico zero |
| Programa normal, a partir de 14h20min17s | Montagem após orientação de troca para o segundo | Dados BMP voltaram a ser persistidos antes do monitor |
| MicroPython, monitor 14h20min31s | Mesma montagem desse momento | 18/18 válidas, RAW e calibração preservados |
| Programa normal após reset | Mesma montagem, sem nova intervenção serial | Mais 17/17 válidas na observação inicial de 90 s; continuidade ampliada até 14h40 |

O monitor das 14h16 leu `60f060000000` inicialmente e `60f140000000` ao final. O ID e a calibração respondiam, mas os três bytes térmicos permaneciam `00 00 00`. Isso mostra por que “encontrar o endereço” e “medir corretamente” são verificações distintas.

O monitor preserva o objeto BMP após uma leitura bruta inválida, enquanto o programa normal tenta reinicializá-lo depois da falha. Essa diferença foi testada e **não recuperou o HW-611 nas janelas de falha**. A nova recuperação já estava presente no programa normal antes do monitor válido; não atribuí-la a essa diferença de tratamento.

Há explicações ainda possíveis: troca efetiva de módulo, contato que mudou durante a reconexão, alimentação/interconexão intermitente ou comportamento interno do componente. Não houve medição com multímetro, osciloscópio ou analisador lógico para escolher uma delas. Não foi comprovado sensor queimado, curto, defeito de solda ou problema exclusivo do ESP32.

## 7. O que os números significam

`temperatura_bmp` é a temperatura interna usada pelo BMP; `temperatura` é a leitura do DHT22. Elas não precisam coincidir exatamente. Na última amostra exportada, foram 23,4 °C e 22,9 °C, respectivamente. Essa diferença sozinha não autoriza ajuste de calibração.

A pressão publicada é a pressão absoluta local calculada pelo driver, sem redução ao nível do mar. Uma previsão meteorológica pode usar outra referência de pressão. Comparar diretamente esses números sem conhecer a referência e a altitude não é uma validação de precisão. A temperatura interna participa da compensação da pressão; substituir por uma temperatura ambiente escolhida não recupera uma conversão térmica inválida. [Bosch, descrição e compensação](https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bmp280-ds001.pdf).

O driver atual rejeita ADC_T igual a `0`, `0x80000` ou `0xFFFFF`, bem como ADC_P nesses valores, e rejeita resultados fora de −40 a 85 °C ou 300 a 1100 hPa. São os critérios do software atual. **ADC zero não significa temperatura ambiente de 0 °C.** Com a calibração anterior, ADC_T=0 produzia aproximadamente −132,73 °C pelo cálculo; isso não era uma temperatura real comprovada. A sentinela `0x80000` de medição omitida também não deve ser confundida com `0x00000`.

LDR=0 significa “Claro” no programa, não 0 lux. MQ-135=393 é uma contagem ADC, não ppm. O relatório não transforma esses dados em grandezas que não foram calibradas.

## 8. Caminho dos dados e interpretação do painel

```text
BMP280 + DHT22 + LDR + MQ-135
              ↓
       MicroPython no ESP32
              ↓ Wi-Fi / POST /api/leituras
       FastAPI no computador
              ↓
       SQLite: data/estacao.db
              ↓ GET a cada 5 s
       http://localhost:8000/
```

O navegador foi verificado às 14h27: mostrava **“Recebendo dados”**, BMP em **23,4 °C / 935,07 hPa**, cartões dos outros sensores e histórico preenchido. A captura está em [painel_142705.png](diagnosticos/referencia_bmp280_20261111/painel_142705.png).

O painel já tinha os campos `pressao` e `temperatura_bmp` ligados à API. Não foi necessário alterar HTML ou JavaScript para a recuperação aparecer. A consulta usa a estação `esp32-01`, os últimos 100 registros e atualização a cada cinco segundos. O alerta de atraso aparece após 30 segundos sem recepção recente.

`bmp_conectado=true` significa medição aceita pelos critérios atuais. `false` significa **sem medição BMP validada**; pode haver comunicação com ID legível mesmo assim. Em falha, `pressao` e `temperatura_bmp` são `null` e aparecem como “—”. O texto “Sensor conectado” do painel não é uma certificação elétrica.

Exemplo real de registro persistido, usado como referência de formato:

```json
{
  "id": 3659,
  "estacao_id": "esp32-01",
  "recebido_em": "2026-11-11T17:40:03.460033+00:00",
  "luz": 0,
  "estado": "Claro",
  "temperatura": 22.9,
  "umidade": 76.6,
  "gas": 393,
  "pressao": 935.0,
  "temperatura_bmp": 23.4,
  "bmp_conectado": true
}
```

O horário é de **recepção no servidor**, em UTC, convertido pelo painel para o fuso do navegador; não é um relógio de aquisição fornecido pelo sensor.

## 9. Se parar: sequência de diagnóstico

### Etapa 1 — Preservar o estado antes de mexer

Anotar a hora, o módulo físico conectado, a última leitura e a mensagem do painel. Tirar foto da montagem mostrando os nomes dos terminais e a posição dos fios. Guardar o histórico/CSV. Alterar uma variável por vez; registrar cada troca. Não começar trocando biblioteca, flash e fios simultaneamente.

### Etapa 2 — Conferir API e dados, sem interromper o ESP32

Na pasta do projeto, executar no PowerShell:

```powershell
Invoke-RestMethod 'http://127.0.0.1:8000/api/saude'
Invoke-RestMethod 'http://127.0.0.1:8000/api/leituras/ultima?estacao_id=esp32-01' |
    Format-List
```

Repetir a segunda consulta após cerca de dez segundos. Comparar `id` e `recebido_em`, além dos dois campos BMP. Um HTTP 200 com uma leitura antiga não comprova que o ESP32 continua enviando.

| Observação | O que verificar em seguida |
| --- | --- |
| API não responde | Processo FastAPI, porta 8000 e endereço usado no navegador |
| API responde, mas ID/horário não avançam | Alimentação/execução do ESP32, Wi-Fi, IP do computador e resultado dos POST |
| Dados novos de DHT/LDR/MQ, mas BMP nulo | Diagnóstico do BMP: a cadeia de envio está funcionando para os demais campos |
| API mostra BMP novo e preenchido, painel não | Recarregar a aba com Ctrl+F5; o painel consulta diretamente a estação `esp32-01` |
| POST 401 | Chave da placa e do servidor; reiniciar o servidor após mudar `.env` |
| POST 503 | Chave ausente na configuração do servidor |
| POST 422 | Campo recusado na resposta, faixa/coerência do payload ou campo obrigatório ausente |
| Timeout de conexão / nenhum POST | Rede, `API_URL`, IP do notebook, firewall e porta |
| ID `0x58` legível, ADC_T sempre zero | Comunicação presente, mas conversão térmica ainda inválida; comparar RAW e calibração |
| Nenhuma resposta em `0x76/0x77` | Montagem, alimentação, SDA/SCL, CSB/SDO e módulo identificado |
| SCL ou SDA lido em nível baixo | Investigar contato/barramento/alimentação; nível lógico sozinho não prova curto |

Se a API estiver encerrada, iniciar **uma única instância** no terminal da raiz do projeto:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --env-file .env
```

Usar `http://localhost:8000/` no notebook. `0.0.0.0` é endereço de escuta do servidor. No ESP32, `API_URL` precisa apontar para o IP local do notebook, não para `localhost`. O hotspot usado durante os testes foi o iPhone de Gustavo; reconectar à rede pode mudar o IP. Conferir com `ipconfig` e a configuração privada local, sem publicar senha/chave no relatório. Não trocar de porta no servidor sem ajustar o destino de envio da placa.

### Etapa 3 — Conferir a montagem, se a falha estiver restrita ao BMP

Com a alimentação desligada, comparar os terminais com a tabela da seção 3, inclusive CSB e SDO. Verificar se o contato mudou de fileira na protoboard e se a etiqueta do módulo corresponde ao teste. Recolocar somente o necessário. Não desmontar os outros sensores como primeira ação.

Se houver instrumento disponível, medir a alimentação **diretamente no módulo**, incluindo durante aquisição. Sem instrumento, registrar essa limitação. Não interpretar um GPIO em 1 como medição de 3,3 V nem forçar diretamente uma linha de sinal em 3V3 para vencer um zero. Não acrescentar resistores sem conferir os já presentes.

### Etapa 4 — Repetir o monitor que gerou a referência

Usar **`scripts/monitorar_bmp280.py`**. Ele foi o teste usado para capturar RAW, calibração e retorno da API juntos. Fechar Thonny e qualquer outro monitor serial. Confirmar a porta por `.\.venv\Scripts\python.exe -m mpremote connect list`; a porta observada nesta sessão foi COM5.

Este comando pausa temporariamente o `main.py`, roda o monitor na RAM e tenta retomar o programa normal com reset no `finally`. Não grava firmware nem substitui arquivos da placa. Durante o teste, o próprio monitor lê os outros sensores e tenta enviar suas medidas reais. O tempo nominal é de 90 segundos, podendo ser ampliado por operações pendentes. [MicroPython, `mpremote run` e reset](https://docs.micropython.org/en/latest/reference/mpremote.html).

Executar somente quando for necessário diagnosticar; **não foi executado novamente para elaborar este relatório**:

```powershell
Set-Location -LiteralPath 'C:\Users\Windows\computer-science\estacao-meteorologica'

$pythonEstacao = Join-Path $PWD '.venv\Scripts\python.exe'
$portaEstacao = 'COM5'
$pastaLogs = Join-Path $PWD '.tools\logs_bmp280'
New-Item -ItemType Directory -Path $pastaLogs -Force | Out-Null
$arquivoLog = Join-Path $pastaLogs ('monitor-' + (Get-Date -Format 'yyyyMMdd-HHmmss-fff') + '.txt')

try {
    & $pythonEstacao -m mpremote connect $portaEstacao soft-reset run scripts\monitorar_bmp280.py 2>&1 |
        ForEach-Object {
            $linhaMonitor = $_.ToString()
            Write-Host $linhaMonitor
            $linhaMonitor
        } | Out-File -LiteralPath $arquivoLog -Encoding utf8
    if ($LASTEXITCODE -ne 0) {
        throw 'O monitor terminou com erro. Consulte o log salvo.'
    }
}
finally {
    & $pythonEstacao -m mpremote connect $portaEstacao reset
    if ($LASTEXITCODE -ne 0) {
        Write-Warning 'Reset nao confirmado. Confira a porta e retome a estacao.'
    }
}

Write-Host ('Log salvo em: ' + $arquivoLog)
```

Se a janela do terminal for encerrada ou a USB desconectada, não presumir que o `finally` conseguiu executar. Após resolver a conexão, retomar com:

```powershell
.\.venv\Scripts\python.exe -m mpremote connect COM5 reset
```

Preferir o Python da `.venv` com `-m mpremote`; não depende de ativar o ambiente ou de um atalho `.exe` criado em outro caminho. Não abrir duas sessões na mesma serial. O script antigo `scripts/diagnosticar_bmp280.py` permanece como histórico, mas alterna HardwareI2C/SoftI2C; não é a primeira opção desta referência.

### Etapa 5 — Ler o resultado e confirmar a retomada

| Campo do monitor | Interpretação útil |
| --- | --- |
| `endereco`, `id` | Endereço utilizado e ID lido; conferir ID `88`/`0x58`, não tratá-los como etiqueta física |
| `raw6`, `adc_t`, `adc_p` | Dados consumidos pelo cálculo daquela tentativa, não valores escolhidos para caber na faixa |
| `cal_inicial_hex`, `cal_cache`, `cal_fresca_hex` | Comparar a referência atual com o que foi lido de novo |
| `cal_coincide_cache` | Confirma consistência entre coeficientes recém-lidos e utilizados; não certifica precisão |
| `dados.bmp_conectado` | Resultado final da validação feita pelo monitor |
| `resultado_driver` | Resultado anterior à checagem adicional de metadados; sozinho não basta |
| `api_ok` | O envio daquele payload foi aceito; pode ser um payload com BMP nulo |
| `bmp_validas` | Medições aceitas pelo monitor; contado antes do POST |
| `api_enviadas` | Total de envios aceitos, incluindo os que tinham BMP nulo |
| `erros`, `inicializacoes` | Separar falha de leitura, de validação, de envio e repetição de inicialização |

Um novo RAW exige nova leitura do barramento. A variação dos ADCs reforça atualização de dados, mas a transação por si só não é uma certificação física do conversor. Se houver falha de leitura, não interpretar metadados ausentes ou um endereço lembrado pelo script como nova detecção.

Após o reset, observar IDs/horários avançando na API por pelo menos mais 90 segundos, com BMP preenchido, outros sensores ativos e atualização no painel. Para avaliar a intermitência já observada, ampliar a janela sem mexer novamente na serial. Guardar também os registros nulos; eles indicam quando a falha voltou.

Se o RAW voltar a `...000000`, conservar o log. Não somar um offset a −132,7 °C, não preencher ADC zero com um número arbitrário, não substituir a temperatura interna por DHT22 e não chamar uma pressão assim calculada de válida. Um scan positivo sozinho não encerra o diagnóstico.

## 10. Como registrar uma nova ocorrência

Copiar e preencher esta ficha antes de mudar a montagem:

| Campo | Preencher na ocorrência |
| --- | --- |
| Data, hora e fuso | |
| Módulo físico e foto dos terminais | |
| Último ID com BMP válido / primeiro ID nulo | |
| Outros sensores continuam chegando? | |
| Mensagem do painel / idade da última recepção | |
| Fonte de alimentação e rede utilizada | |
| SDA / SCL / CSB / SDO e pull-ups presentes | |
| O que mudou imediatamente antes da falha | |
| ID, calibração, RAW, ADC_T e ADC_P do reteste | |
| Resultado de rede/API separado da medição BMP | |
| Uma intervenção realizada e horário dela | |
| Resultado após reset e duração acompanhada | |

Se trocar o módulo, abrir uma nova ficha. Comparar outro módulo nas mesmas ligações ajuda a investigar, mas uma reconexão também altera contatos e alimentação; não atribuir automaticamente a mudança somente ao chip.

## 11. Arquivos preservados com este relatório

Pasta de evidências: [diagnosticos/referencia_bmp280_20261111](diagnosticos/referencia_bmp280_20261111/README.md).

| Arquivo / grupo | Conteúdo e utilidade |
| --- | --- |
| `continuidade_banco.json` | Exportação coerente, somente leitura, dos 217 registros, resumo e amostras históricas selecionadas |
| `leituras_desde_recuperacao.csv` | Os mesmos 217 registros, para abrir em planilha; UTF-8 com BOM, separador `;` |
| `amostras_20261111_142031.jsonl` | As 18 tentativas válidas completas, uma por linha, com RAW/calibração/retorno API |
| `amostras_20261111_141604.jsonl` | As 18 falhas com HW-611 confirmado naquele teste |
| `amostras_20261111_133700.jsonl` | Outra janela anterior de 18 leituras térmicas zeradas |
| `resumos_monitores.json` | Resumos, contexto de identificação e hashes dos logs de origem |
| `contexto_*.json` | Registros originais de contexto e observação após reset dos testes que os geraram |
| `fontes/` | Cópias dos fontes públicos locais usados como referência, sem `config.py` ou `.env` |
| `painel_142705.png` | Captura da página renderizada com dados reais |
| `manifesto_sha256.json` | Tamanhos e hashes para conferir se as evidências foram alteradas |

Os logs originais completos continuam em `.tools/arduino-bmp280/`. As cópias JSONL preservam as 18 amostras estruturadas de cada janela; os marcadores de início/fim estão nos resumos. A pasta `.tools` é excluída das entregas, por isso as evidências selecionadas foram preservadas também em `diagnosticos/`.

Os fontes foram copiados **do computador**, sem abrir novamente a serial. Não equivalem a uma releitura atual de cada arquivo da placa. A restauração anterior já havia verificado a flash e os 14 arquivos do ESP32; não houve nova gravação de firmware para a recuperação ou para este relatório.

As evidências são uma fotografia até o corte da exportação. Novos registros continuam sendo recebidos no banco ativo. **Não substituir `data/estacao.db` por CSV, JSON ou por um snapshot antigo**: isso perderia registros posteriores. A estação também não possui fila offline para recuperar amostras que nunca foram aceitas pelo servidor.

O backup integral anterior ao Arduino permanece no diretório privado `backup_esp32/antes_arduino_20261111_123005`, incluindo duas imagens de flash conferidas e configurações. A restauração integral não é a primeira medida para uma falha de sensor e deve seguir os verificadores do projeto. Esse backup contém credenciais e não acompanha a pasta pública de evidências.

## 12. Fontes e relatórios complementares

As constatações deste documento vêm dos logs locais, exportação SQLite, fonte do projeto e página renderizada. As referências técnicas explicam o funcionamento esperado e não comprovam a causa física da falha:

- [Bosch BMP280, datasheet revisão 1.26](https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bmp280-ds001.pdf): compensação, mapa de registros, interface e montagem I²C.
- [Espressif, interface I²C](https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-reference/peripherals/i2c.html#introduction): características do barramento e pull-ups.
- [MicroPython, mpremote](https://docs.micropython.org/en/latest/reference/mpremote.html): execução temporária, comandos e reset.
- [MicroPython, machine.I2C](https://docs.micropython.org/en/latest/library/machine.I2C.html): API de barramento e timeout do SoftI2C.
- [DIAGNOSTICO_BMP280.md](DIAGNOSTICO_BMP280.md): histórico de alterações de pinagem e retestes.
- [RELATORIO_BMP280_PROFESSOR.md](RELATORIO_BMP280_PROFESSOR.md): histórico específico do módulo identificado como do professor, com ressalva de atribuição.
- [TESTE_ARDUINO_BMP280.md](TESTE_ARDUINO_BMP280.md): teste independente Arduino e restauração comprovada.
- [README.md](README.md): instalação, arquivos e contrato da API da estação.

**Referência prática para um próximo diagnóstico:** preservar módulo, ligação, RAW, calibração, horário e novos IDs do banco. O funcionamento está comprovado na janela acima; a causa exata da recuperação permanece aberta.
