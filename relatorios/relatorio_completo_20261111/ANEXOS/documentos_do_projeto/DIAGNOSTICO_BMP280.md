# Diagnostico do BMP280

Relatorio detalhado do modulo do professor: `RELATORIO_BMP280_PROFESSOR.md`.

Referencia consolidada apos a recuperacao, com evidencias preservadas e procedimento para uma nova falha: [RELATORIO_FUNCIONAMENTO_E_RECUPERACAO_BMP280.md](RELATORIO_FUNCIONAMENTO_E_RECUPERACAO_BMP280.md).

## Leituras recuperadas no reteste de 11/11/2026, 14h20

Apos orientar a troca para o segundo modulo, o usuario respondeu "pode ir".
Esse e o contexto da identificacao deste reteste; nao houve identificacao
eletronica individual nem confirmacao visual remota do componente.

O mesmo monitor MicroPython em RAM, com SDA21/SCL22 e SoftI2C a 50 kHz,
registrou 18 medicoes validas em 18 tentativas, durante 90.001 ms. Os 18
envios foram aceitos pela API, com temperatura BMP de 23,5 a 23,6 C e pressao
de 935,00 a 935,09 hPa. Houve uma unica inicializacao e nenhum erro registrado.
ADC_T variou entre 520456 e 520776, e ADC_P entre 393756 e 393861.

A calibracao lida foi a mesma nas 18 tentativas, igual ao cache do calculo:

```text
266d276918fc7d9520d6d00b9f130e01f9ff8c3cf8c67017
```

Ela difere da referencia registrada anteriormente para o HW-611. Essa
comparacao e uma evidencia de contexto, nao um numero de serie nem uma forma
de atribuir os registros antigos a um modulo especifico.

O primeiro RAW `6028507f2480`, recalculado independentemente com esses
coeficientes, produz 23,5898179 C e 935,0129146 hPa, coerentes com os valores
arredondados pelo driver. O ultimo RAW foi `6021e07f1080`. Esta verificacao
confirma coerencia do calculo, sem certificar exatidao metrologica.

Depois do reset, o `main.py` original voltou a publicar medicoes BMP: registro
3470 as 14:22:41 (UTC-3), 23,5 C e 935,09 hPa. Nao foi necessario gravar
firmware nem alterar o codigo da placa neste reteste. O log completo e o resumo
JSON ficam em `.tools/arduino-bmp280/monitor_bmp280_20261111_142031.*`.

Na observacao adicional de 90 segundos, feita somente pela API sem abrir a
serial, foram persistidos mais 17 registros, IDs 3471 a 3487: todos com BMP
preenchido, sem falhas nessa janela. O ultimo, as 14:24:14 (UTC-3), continha
23,5 C e 935,01 hPa. O programa original permaneceu em execucao. Essa janela
confirma continuidade apos o reset, sem estabelecer estabilidade permanente.

## Teste Arduino e retorno ao MicroPython em 11/11/2026

Comparacao concluida com a biblioteca original Adafruit 3.0.0 em Arduino-ESP32
2.0.17: 179 amostras em 180 segundos, todas com ADC de temperatura zero e
aproximadamente -132,730 C calculados. ID e calibracao coincidiram com a
referencia do HW-611 do professor. Isso afasta uma causa exclusiva da formula
Python, sem determinar a causa fisica. A estacao tambem apresentou uma janela
de medidas plausiveis no MicroPython antes desse ensaio. A atribuicao ao HW-611
se baseou na identificacao informada pelo usuario durante o teste. Posteriormente,
ele levantou a possibilidade de uma troca com o segundo modulo. Como o banco
nao identifica fisicamente o BMP, essa janela nao comprova sozinha intermitencia
do HW-611.

O backup completo da flash foi restaurado e verificado; os 14 arquivos da placa
mantiveram seus hashes e a API retomou novas gravacoes dos demais sensores.
Apos o usuario desfazer a inversao SDA22/SCL21 e confirmar SDA21/SCL22, o modulo
respondeu em 0x76/ID58 nas cinco tentativas, mas ADC_T permaneceu zero nas cinco.
Firmware normal retomado ao final. Detalhes: `TESTE_ARDUINO_BMP280.md`.

## Reteste do segundo modulo em 11/11/2026

O usuario confirmou que conectou o segundo modulo. O HW-611 e o modulo do
professor; os resultados abaixo pertencem ao segundo, nao comprovam recuperacao
do HW-611.

- Antes de interromper o firmware, a API ja recebia medicoes validas.
- Foram persistidas 13 leituras consecutivas, IDs 2334 a 2346, entre 11:46:43 e
  11:47:52, horario de Brasilia (UTC-3). Temperatura BMP: 28,8 a 25,3 C; pressao:
  936,82 a 936,89 hPa. O DHT permaneceu perto de 22,8 C. Isso comprova aquisicao
  operacional nesse intervalo, sem certificar precisao ou estabilidade longa.
- Durante uma consulta posterior, apos inicializar/desinicializar I2C(0) e
  selecionar SoftI2C, SDA21/SCL22 foram lidos altos, mas 0x76 e 0x77 retornaram
  ENODEV. Nao foi possivel obter a calibracao do segundo para comparacao.
- As medicoes BMP seguintes voltaram a nulo. Em consultas posteriores usando
  apenas SoftI2C/entradas com pull-up, SDA21 ficou em 1 e SCL22 em 0. A busca foi
  interrompida quando a linha baixa foi observada.
- O comando de hard reset do ESP32 foi executado; o firmware normal e os demais
  sensores retomaram. O BMP nao se recuperou apos esses resets. Nenhum arquivo
  do ESP32 foi alterado neste reteste.
- A sequencia temporal nao identifica a causa. Alimentacao, contato, modulo e
  eventual interacao do diagnostico com o barramento continuam em investigacao.
  Nao forcar SCL em nivel alto para vencer o zero.
- O usuario realizou o isolamento de SCL no lado do modulo, desligando e
  religando a alimentacao conforme solicitado. Mantendo apenas Pin.IN/PULL_UP,
  sem inicializar I2C, SDA21 e SCL22 ficaram em 1 nas cinco verificacoes.
  O D22 conseguiu subir nessa condicao; isso nao prova curto interno no modulo
  nem certifica todas as caracteristicas do GPIO. Desconexao e ciclo de energia
  ocorreram juntos, portanto seus efeitos ainda nao foram separados.
- Apos o usuario reconectar SCL com a alimentacao desligada e religar, foram
  observadas seis novas leituras da API durante 35 segundos, todas sem BMP.
  Uma consulta somente com Pin.IN/PULL_UP mostrou SDA21/SCL22 em 1 nas cinco
  verificacoes. Portanto, nao foi demonstrado que o modulo mantenha SCL sempre
  baixo quando conectado.
- Na consulta seguinte usando apenas SoftI2C, SCL estava em 1 apos inicializar
  o barramento e apos cada tentativa, mas 0x76/0x77 retornaram ENODEV. Nao basta
  observar nivel alto para comprovar que o sensor esteja comunicando.
- Firmware normal retomado por hard reset. Proximo dado solicitado: tensao
  VCC-GND medida diretamente no segundo modulo com multimetro em tensao continua.
  Nao adicionar componentes ou declarar curto/defeito sem essa investigacao.
- A pedido do usuario, um reteste posterior usando somente SoftI2C a 50 kHz
  realizou cinco observacoes: nas duas primeiras, SDA/SCL altos, mas 0x76/0x77
  sem resposta (ENODEV); nas tres seguintes, SDA alto e SCL baixo, sem novas
  transacoes. O estado continua intermitente, sem causa fisica determinada.
  Firmware reiniciado ao final; registro 2447, recebido as 11:59:48 (UTC-3),
  confirmou os demais sensores persistidos e BMP nulo. Nenhuma medida fisica de
  tensao foi fornecida; niveis logicos nao substituem essa medida.

## Montagem e historico anterior

Montagem atual: SDA no GPIO21, SCL no GPIO22, VCC e CSB em 3V3,
GND e SDO em GND. O endereco esperado com SDO baixo e 0x76.
O modulo HW-611 possui seis pinos; siga as etiquetas de cada placa,
pois o lado em que o conector foi soldado altera a orientacao visual.

O LDR foi transferido do GPIO21 para o GPIO18, conforme confirmado pelo usuario.
O DHT22 permaneceu no GPIO4 e respondeu a duas medicoes de temperatura/umidade.
O MQ-135 continua no GPIO34. A pinagem do main e dos defaults dos sensores foi
atualizada. Os testes antigos com SDA18 descritos abaixo sao historicos.
O perfil adicional temperatura x2/pressao x16/filtro x16/standby500ms tambem foi
testado no SDA21, com CTRL=57 e CONFIG=90 aceitos; temperatura bruta ainda zero.

## O que foi confirmado

- O primeiro modulo responde em 0x76 com ID 0x58 e coeficientes legiveis.
- A temperatura bruta permanece 000000, inclusive em leituras separadas
  dos registradores FA, FB e FC. Zero bruto nao significa 0 graus Celsius.
- Foram testados reset, espera, modo normal e forcado, temperatura isolada,
  resolucoes x1/x2/x16 e radio Wi-Fi desligado.
- O perfil usado pela Adafruit (config 00, controle B7) tambem retornou
  temperatura zerada. Foi testada a configuracao equivalente, sem instalar
  Arduino/CircuitPython ou apagar o firmware MicroPython da placa.
- Ao desabilitar temperatura, o modulo retorna 800000, o marcador esperado;
  ao habilita-la, retorna 000000. A configuracao e aceita, mas a medicao
  termica continua invalida.
- Foram adicionados resistores de 4,7 kOhm entre SDA/3V3 e SCL/3V3.
  O teste posterior continuou retornando temperatura bruta zero.
- Outro modulo chegou a fornecer 23,3 graus Celsius e 938,12 hPa,
  mas depois houve perda de comunicacao. Isso nao valida todos os modulos
  e nao prova que todos estejam defeituosos.

Uma linha lida como baixa nao prova curto ao GND nem defeito no GPIO.
Essas causas exigem medicao e isolamento fisico. As conclusoes anteriores
que condenaram o sensor ou afirmaram curto definitivamente eram fortes demais.

## Correcao do firmware

O programa normal inicialmente usava SCL18/SDA19 apesar dos testes com SDA18/SCL22.
Uma correcao intermediaria usou SDA18/SCL22. A montagem definitiva passou para
SDA21/SCL22, com o LDR transferido para D18; agora `main.py` usa
`SensorBMP280(scl=22, sda=21)` explicitamente.
O driver usa SoftI2C a 50 kHz com timeout de espera do clock (clock stretching) de 5 ms,
reset/espera da calibracao e medicao forcada com temperatura x2/pressao x16.
A espera da conversao tem limite de 1 segundo.

Coeficientes de fabrica invalidos, ADC zero/ignorado/saturado e resultados
fora da faixa sao rejeitados antes do POST. O wrapper retorna valores BMP
nulos e bmp_conectado falso, preservando as leituras dos outros sensores.
Isso evita que -132,7 graus Celsius cause 422 e bloqueie o lote inteiro.
O campo bmp_conectado passa a indicar uma medicao valida, alem da deteccao.
O driver tenta novamente depois de cinco segundos.

Estas correcoes nao garantem recuperar a conversao termica do modulo atual.
Pressao bruta variando sem temperatura valida nao e pressao compensada validada.
Nao foi aplicado offset artificial nem usada a temperatura do DHT22 no lugar
da temperatura interna do BMP280.

## Validacao sem codigo do professor

O BMP280 possui calibracao individual de fabrica; nao exige equilibragem manual
para produzir temperatura bruta valida. Os coeficientes nao devem ser alterados
para forcar um resultado desejado. O calculo do driver e verificado com um
vetor numerico de teste: ADC_T 519888 e ADC_P 415148 produzem
aproximadamente 25,08 graus Celsius e 1006,53 hPa com os coeficientes
fixados no teste (eles nao substituem os coeficientes de cada modulo real).
Os testes em `tests/test_bmp280.py` verificam esse calculo, timeout, rejeicao de
valores invalidos, recuperacao e aceite da API com BMP nulo e DHT/MQ validos.

Na validacao da atualizacao, os 12 testes automatizados passaram. O driver
atualizado foi enviado a COM5 com copia de seguranca dos arquivos anteriores
em backup_esp32. Na placa, ele retornou 'Temperatura bruta invalida: 0x0'
e os campos BMP nulos, como esperado. A resolucao fisica continua pendente.

O usuario precisa manter os demais sensores montados. Os testes seguintes foram
feitos com essa montagem intacta, sem exigir o codigo do professor:

- Temperatura em todas as resolucoes x1/x2/x4/x8/x16: ADC sempre zero.
- Leitura com STOP separado, repeated START e readfrom_mem: mesmo resultado.
- Modo normal B7 por 12 segundos, sem reinicializar o sensor entre amostras:
  temperatura sempre zero, enquanto a pressao bruta varia.
- Buffer preenchido com AA antes da leitura: o dispositivo substitui os tres
  bytes por 000000. Nao e apenas um buffer inicializado com zeros no programa.
- Linhas altas mesmo sem pull-ups internos do ESP32 no momento do teste.
- Usuario confirmou apenas um BMP280 conectado; nao ha evidencia de colisao
  entre os tres modulos testados.

O numero -132,7 e reproduzido matematicamente ao usar ADC_T=0 e os coeficientes
termicos (27348, 25466, 50) do primeiro modulo. Ele nao descreve a temperatura
real da casa. Nenhuma configuracao testada recuperou a conversao termica.
Isso nao determina sozinho a causa fisica nem prova que os tres modulos
tenham o mesmo defeito. Medir a tensao nos pinos do modulo e inspecionar soldas
continua sendo util; nao foi feita medicao eletrica com multimetro remotamente.

O script independente `scripts/diagnosticar_bmp280.py` permite repetir o teste
por USB, mantendo a montagem. Consulte `COMO_EXECUTAR.md`. O firmware ja usa a
pinagem atual e informa a falha no console. A comprovacao de funcionamento
exige temperatura bruta valida e novas leituras BMP validas no banco.

## Fontes

- Bosch, datasheet BMP280, secoes 3.3, 3.11 e 4.3:
  https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bmp280-ds001.pdf
- Adafruit, implementacao da biblioteca e configuracao padrao:
  https://github.com/adafruit/Adafruit_BMP280_Library
- Relato do autor de driver sobre alguns HW-611 (nao e diagnostico deste modulo):
  https://github.com/lawslefthand/Stm32F0-LL-BM280-Driver#known-bugs
