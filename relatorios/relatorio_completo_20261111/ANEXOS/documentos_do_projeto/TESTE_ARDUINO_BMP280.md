# Teste temporário do BMP280 com Arduino e Adafruit

## Objetivo e identificação

Em 11 de novembro de 2026, foi executado um teste independente do firmware
MicroPython para comparar o módulo HW-611 identificado pelo usuário como o
BMP280 do professor. O objetivo foi verificar se a temperatura bruta zerada
dependia exclusivamente da implementação Python ou da ausência da biblioteca
Arduino. A marcação da placa, o endereço e o identificador eletrônico não
certificam autenticidade Bosch nem identificam individualmente um componente.

O teste manteve os outros sensores montados. O programa Arduino foi temporário,
sem conexão à API; durante sua execução, a estação deixou de enviar medições.

## Ambiente registrado

| Componente | Configuração |
| --- | --- |
| Arduino CLI | 1.6.0 |
| Arduino-ESP32 | 2.0.17 |
| Adafruit BMP280 Library | 3.0.0 |
| esptool | 5.6.0 |
| Placa/FQBN | ESP32 Dev Module, `esp32:esp32:esp32` |
| Flash | DIO, 40 MHz, 4 MB, sem PSRAM |
| I²C do sketch | SDA GPIO21, SCL GPIO22, 100 kHz |
| Serial | 115200 baud |

Foram mantidos os parâmetros padrão da biblioteca Adafruit durante toda a
captura: modo normal, temperatura e pressão com sobreamostragem ×16 e filtro
desligado. Os registros mostraram `F3/F4/F5=0CB700`, incluindo controle `B7` e configuração
`00`. O estado `0C` foi registrado como dado, sem interpretá-lo como um código
de defeito do sensor.

## Captura e resultados

A captura de 180 segundos começou em `2026-11-11T15:56:48.931Z`, equivalente a
12:56:48.931 no fuso UTC−3. Foram reconstruídas 179 amostras do log serial,
associando o bloco bruto de seis bytes às contagens ADC e aos resultados
calculados. O contador do ESP32 também registrou 179 amostras inválidas.

| Evidência | Resultado |
| --- | --- |
| Inicializações Adafruit bem-sucedidas | 1 |
| ID no registrador `D0` | `58` |
| Amostras com ADC térmico zero | 179 de 179 |
| Amostras consideradas plausíveis | 0 |
| Erros das leituras I²C diagnósticas próprias | 0 |
| Temperatura calculada pela Adafruit | aproximadamente −132,730 °C |
| ADC de pressão mínimo/máximo | 398488 / 399393 |
| Primeiro bloco `F7..FC` | `6164B0000000` |
| Último bloco `F7..FC` | `614C60000000` |

Os coeficientes de 24 bytes foram lidos como:

```text
D46A7A633200B9946ED6D00BD513F9FFF9FF8C3CF8C67017
```

Esse bloco coincide com a referência histórica do módulo do professor. Nas
amostras, os três primeiros bytes representavam pressão e os três últimos
permaneceram `000000`, referentes à temperatura. Contagens ADC não são valores
em graus Celsius ou hectopascais.

O valor de −132,730 °C é produzido pela compensação aplicada ao ADC térmico
zero; não representa a temperatura do ambiente. Valores calculados de pressão
na ordem de 716 hPa também não foram aceitos como pressão atmosférica válida,
pois a compensação depende da temperatura interna. Não se aplicou correção
artificial nem temperatura externa para apresentar uma leitura aparentemente
normal.

## Alcance da comparação

O resultado não é exclusivo da fórmula Python: a biblioteca Adafruit original,
executada no ambiente Arduino, também encontrou temperatura bruta zero nessa
janela. Isso não determina a causa física. Alimentação no ponto do módulo,
interconexões e funcionamento interno permanecem possibilidades; não houve
medição de VCC durante conversão com instrumento.

O código diagnóstico próprio verificava transmissão e quantidade de bytes.
Ausência de erros nessas consultas não certifica todas as transações internas
da biblioteca. A Adafruit interpreta corretamente T1/P1 como valores sem sinal
e os demais coeficientes como valores com sinal; isso não valida, por si só, a
exatidão dos coeficientes. As consultas brutas e os cálculos da biblioteca são
transações distintas e podem corresponder a aquisições consecutivas.

Os períodos anteriores com valores plausíveis no MicroPython continuam
registrados. A atribuição ao HW-611 se baseou na identificação informada pelo
usuário naquele momento; posteriormente, ele levantou a possibilidade de uma
troca com o segundo módulo. O banco não registra qual BMP estava conectado,
portanto esses períodos não comprovam isoladamente funcionamento anterior do
HW-611. O teste Arduino também não demonstra que esse módulo jamais funcione.

## Backup e restauração comprovada

Antes da gravação foram preservadas duas leituras integrais de 4 MB da flash,
ambas a 115200 baud, com tamanho e SHA-256 iguais:

```text
C52BE2D30FD954D265346E2C6A186551EDBC2BBAB2F9421B41561B9F62921EED
```

O backup privado local `backup_esp32/antes_arduino_20261111_123005` contém 41
arquivos de fontes/configurações e snapshot SQLite com 2768 registros e
integridade confirmada. Os 14 arquivos do sistema de arquivos da placa tiveram
hashes iguais antes e depois da restauração. O esptool confirmou a verificação
integral da flash restaurada, e o MicroPython voltou a iniciar.

Após a restauração, os registros da API avançaram de 2832 para 2834, com os
outros sensores preenchidos e campos BMP nulos. O banco original continuou
preservado; não foi revertido ao snapshot anterior. Antes do ensaio de hardware,
25 testes Python haviam passado. Eles verificam software, não precisão física.

Não ficou firmware Arduino instalado permanentemente. Os artefatos de compilação
e o log ficam em `.tools`, diretório de ferramentas ignorado; a unidade temporária
`R:` usada na compilação foi removida. Imagens privadas da flash e configurações
com credenciais não devem acompanhar entregas compartilháveis.

## Informação posterior sobre os fios

Depois do teste, o usuário informou SDA no D22 e SCL no D21 e pediu a reversão.
O código restaurado utiliza SDA21/SCL22. Após o usuário confirmar a reconexão
física nessa ordem, o reteste MicroPython recebeu resposta em `0x76`, ID `0x58`
e a mesma calibração nas cinco tentativas. SDA e SCL ficaram altas nas cinco
verificações. Todas as cinco aquisições ainda retornaram ADC térmico zero:
`611670000000`, `611850000000`, `6118c0000000`, `611940000000` e `611a80000000`.

A comunicação foi recuperada nessa ligação; a medição térmica permaneceu
inválida. O firmware normal foi retomado e a API persistiu o registro 2882 às
13:13:09 (UTC−3), com os outros sensores preenchidos e BMP nulo. O campo
`bmp_conectado=false` significa ausência de medição validada, mesmo quando o
ID do dispositivo pode ser lido.

Esse relato posterior não deve ser aplicado retroativamente à captura Arduino:
os resultados documentam a montagem que respondeu durante cada janela. A
correção dos fios não demonstrou recuperação definitiva do ADC térmico.

## Nova observação MicroPython sem reinicialização entre amostras

Em 11/11/2026, por volta de 13h37 (UTC−3), foi executado
`scripts/monitorar_bmp280.py` somente na RAM, com SDA21/SCL22 e SoftI2C a
50 kHz. Ao contrário do tratamento normal de falhas, o monitor manteve o
mesmo objeto BMP280 depois de receber ADC térmico zero. Assim, as tentativas
seguintes dispararam outra conversão forçada sem reiniciar o sensor nem
recarregar sua calibração. Nenhum arquivo da placa ou firmware foi gravado.

O registro captura o bloco bruto usado pela mesma chamada que calcula a
medição; as consultas posteriores de ID e calibração não substituem esse bloco.
O resultado foi:

- Duração medida de 90.001 ms, 18 tentativas e uma única inicialização.
- Resposta em `0x76`, ID `0x58` e calibração fresca igual à utilizada pelo
  cálculo nas 18 tentativas.
- ADC térmico zero em todas as tentativas; nenhuma medição BMP válida.
- Contagens brutas de pressão entre 397306 e 397516. Primeiro bloco
  `610cc0000000`; último `60ffa0000000`. Essa variação não valida a pressão
  compensada quando o canal térmico permanece inválido.
- Os outros sensores continuaram sendo lidos: os 18 envios à API tiveram
  sucesso, com campos BMP nulos.

O log completo ficou em
`.tools/arduino-bmp280/monitor_bmp280_20261111_133700.log`.
Após o monitor, foi executado o reset da placa para retomar o `main.py`
original. A API recebeu o registro 3160 às 13:38:48 (UTC−3), com temperatura
ambiente de 23,4 °C, umidade de 72,9%, luz 0 e gás 315; o BMP continuava sem
medição validada. A temperatura ambiente pertence ao outro sensor.

Portanto, evitar reinicializações entre tentativas não recuperou os dados
nessa janela. Isso confirma comunicação com o dispositivo durante o teste,
mas não permite distinguir sozinho uma falha de interconexão, alimentação
ou funcionamento interno do módulo. As leituras plausíveis do histórico
continuam preservadas e não foram reproduzidas nesta observação.

### Reteste às 14h16, com identificação confirmada pelo usuário

Em 11/11/2026, o usuário confirmou **HW-611 do professor** durante a nova
execução do mesmo monitor em RAM, com SDA21/SCL22. Em 90.001 ms ocorreram
18 tentativas: todas responderam em `0x76`, ID `0x58`, com calibração fresca
igual ao cache, mas ADC térmico zero. Nenhuma medição BMP foi validada. As
contagens brutas de pressão variaram de 397033 a 397132, com blocos inicial
`60f060000000` e final `60f140000000`. Os 18 envios dos outros sensores à API
tiveram sucesso. A identificação física foi informada pelo usuário; o ID do
chip não é um número de série individual.

O log `monitor_bmp280_20261111_141604.log` e o resumo de mesmo nome com extensão
`.json` ficam em `.tools/arduino-bmp280/`. O reset final terminou com sucesso,
e o programa normal voltou a enviar: registro 3418 às 14:17:59 (UTC−3), com
DHT22 em 23,1 °C e 77,0%, gás 249 e BMP nulo. Nenhum firmware foi gravado
neste reteste.

## Referências primárias

- [Bosch Sensortec: datasheet BMP280](https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bmp280-ds001.pdf), aquisição, calibração e compensação.
- [Adafruit: biblioteca BMP280](https://github.com/adafruit/Adafruit_BMP280_Library), implementação e parâmetros padrão.
- [Espressif: comandos esptool](https://docs.espressif.com/projects/esptool/en/latest/esp32/esptool/basic-commands.html), leitura, escrita e verificação de flash.
