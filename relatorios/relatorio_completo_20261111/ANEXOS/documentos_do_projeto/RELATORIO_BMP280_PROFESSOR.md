# Relatório técnico — BMP280 do professor

**Projeto:** estação meteorológica com ESP32, MicroPython, FastAPI e SQLite.  
**Elaboração:** 11 de novembro de 2026.  
**Fuso de referência:** America/Sao_Paulo, UTC−3.  
**Objeto:** primeiro módulo, identificado pelo usuário como o BMP280 do professor.  
**Situação atualizada:** houve medições plausíveis no MicroPython, atribuídas ao HW-611 pela identificação informada durante o teste. Essa atribuição física permanece incerta; o banco identifica a estação, sem identificar qual módulo BMP estava conectado. Os testes diretos recentes continuam mostrando temperatura bruta zero.

## Atualização de 11/11/2026, antes do teste Arduino

**Nota posterior, 14h20:** após orientar a troca para o segundo módulo, um novo
teste MicroPython recebeu 18 de 18 medições válidas, com um bloco de calibração
diferente da referência do HW-611. O programa normal também voltou a publicar
dados BMP depois do reset. O resultado pertence à montagem desse novo teste;
não comprova recuperação do HW-611 nem identifica retroativamente o módulo
das janelas antigas. Os dados e o contexto de identificação estão em
[DIAGNOSTICO_BMP280.md](DIAGNOSTICO_BMP280.md).

Na ocasião, o usuário informou que o módulo conectado era o **HW-611 do
professor**. A API recebeu pelo menos nove leituras consecutivas, IDs 2652 a
2660, entre **12:19:08 e 12:19:52 (UTC−3)**, com temperatura BMP entre 23,8 e
23,9 °C e pressão entre 936,21 e 936,25 hPa. A partir do ID 2661, às 12:19:57,
o BMP voltou a aparecer sem medição. Nenhuma consulta serial foi executada
durante essa janela observada na API.

Essas medições foram produzidas pelo firmware MicroPython existente, antes de
qualquer gravação Arduino. Elas mostram aquisição de valores plausíveis na
estação; não certificam precisão metrológica, procedência do chip ou estabilidade
prolongada. Posteriormente, o usuário levantou a possibilidade de uma troca
entre o HW-611 e o segundo módulo durante os testes. Como esses registros não
contêm identificação física nem calibração do BMP, não é possível comprovar
retroativamente qual módulo originou essa janela.

Portanto, a descrição de temperatura bruta sempre zerada nas seções históricas
não deve ser interpretada como um estado permanente comprovado. O diagnóstico
passou a incluir **intermitência**, cuja causa ainda não foi determinada.

A comparação temporária com Arduino foi executada depois de duas cópias
integrais da flash de 4 MB terem sido conferidas como idênticas. A biblioteca
Adafruit original registrou **179 amostras em três minutos, todas com ADC
térmico zero**, repetindo aproximadamente −132,730 °C no cálculo. O MicroPython
foi restaurado integralmente: a flash foi verificada e os 14 arquivos da placa
tiveram os mesmos hashes de antes do teste. Novas gravações na API foram
confirmadas; o banco do computador não foi revertido ao snapshot.

Após uma inversão posterior dos fios ser desfeita, SDA21/SCL22 voltaram a
permitir ler ID e calibração em cinco tentativas. A temperatura bruta continuou
zerada. O relato completo, os limites dessa comparação e a restauração estão
em [TESTE_ARDUINO_BMP280.md](TESTE_ARDUINO_BMP280.md).

## 1. Resultado principal

O módulo responde no endereço I²C `0x76`, retorna o identificador `0x58` e permite ler seus coeficientes. Na última sequência direta, SDA e SCL permaneceram em nível lógico alto em repouso. Portanto, não se trata simplesmente de um dispositivo que nunca respondeu ao ESP32.

Entretanto, os três bytes de temperatura permaneceram em `00 00 00`. A contagem bruta de temperatura, chamada `ADC_T`, foi zero em sucessivas leituras e configurações. Os registradores de pressão apresentaram contagens diferentes de zero e variaram entre amostras.

**Conclusão sustentada:** há comunicação digital com o módulo, mas não foi obtida uma amostra térmica utilizável na montagem examinada. A pressão compensada também não foi validada, pois seu cálculo utiliza a temperatura interna.

A causa exata permanece indeterminada. Não foi comprovado que o componente esteja queimado, que exista curto em uma solda específica ou que a alimentação esteja correta durante toda a conversão.

## 2. Contexto, escopo e limitações

O projeto começou com um único programa MicroPython executado pelo Thonny. Foi reorganizado em módulos de sensores, programa principal no ESP32, API FastAPI no computador, banco SQLite e painel web. O diagnóstico do BMP280 foi feito antes do envio à API, lendo diretamente os registradores pela porta serial.

O usuário informou que este módulo havia funcionado no ESP32 do professor. Esse funcionamento anterior não foi observado diretamente nesta investigação, e o código utilizado não estava disponível. O relato foi considerado uma pista para fazer testes comparativos, não uma comprovação independente da integridade atual do módulo.

Foram usados comandos por USB, revisão dos arquivos e inspeção de fotos. Não houve medição com multímetro, osciloscópio ou analisador lógico. A montagem dos demais sensores foi preservada. Leituras digitais de GPIO não equivalem a medições de tensão, resistência ou forma de onda.

Três módulos foram examinados ao longo da sessão. Os resultados dos outros dois são separados neste relatório para evitar atribuir ao módulo do professor uma falha observada durante outra troca. Ensaios realizados antes de uma troca ser confirmada não foram usados para identificá-lo.

## 3. Identificação do hardware e montagem atual

| Item | Identificação observada |
| --- | --- |
| Microcontrolador | ESP32; firmware informou `Generic ESP32 module with ESP32` |
| Ambiente da placa | MicroPython 1.29.0, conforme consulta realizada na sessão |
| Porta serial | COM5 nas verificações registradas |
| Interface USB | Silicon Labs, VID/PID `10c4:ea60` |
| Placa do sensor | HW-611, seis pinos, marcação `280` nas fotos |
| Modelo compatível com o ID | BMP280 |
| Endereço encontrado | `0x76` |
| ID lido no registrador `0xD0` | `0x58` |

O identificador USB pertence à interface serial, não ao BMP280. O endereço I²C e o ID do chip não são números de série individuais nem comprovação de autenticidade do fabricante.

### 3.1 Pinagem vigente

| Dispositivo/sinal | Ligação atual |
| --- | --- |
| BMP280 SDA | GPIO21 / D21 |
| BMP280 SCL | GPIO22 / D22 |
| BMP280 VCC | 3V3, conforme montagem informada |
| BMP280 GND | GND comum |
| BMP280 CSB | 3V3 na configuração de seis fios |
| BMP280 SDO | GND na configuração de seis fios |
| LDR, saída digital | GPIO18 / D18 |
| DHT22, sinal | GPIO4 / D4 |
| MQ-135, saída analógica | GPIO34 / D34 |

O LDR usava inicialmente o GPIO21 e foi transferido para o GPIO18. O usuário confirmou que o fio movido era do sensor de luz. O DHT22 permaneceu no GPIO4 e respondeu com temperatura e umidade válidas.

Historicamente, o módulo também foi examinado em SCL19/SDA18 e SCL22/SDA18. O par original SCL18/SDA19 não correspondia à ligação que primeiro permitiu detectá-lo. Essas etapas pertencem ao histórico; o firmware atual usa explicitamente SDA21/SCL22.

O lado em que o pente foi soldado muda a orientação visual da placa. As ligações devem seguir os nomes impressos, sem copiar automaticamente a ordem dos cabos de um módulo diferente.

### 3.2 Pull-ups e alimentação

O usuário informou instalar dois resistores com faixas amarelo, violeta, vermelho e dourado: 4,7 kΩ, tolerância de 5%. A ligação prevista é um resistor entre SDA21 e 3V3 e outro entre SCL22 e 3V3. Eles são derivações dos sinais, não componentes em série nos fios.

A posição física final desses resistores e a tensão real no módulo não foram certificadas por instrumento. Em um ensaio, as linhas foram observadas altas mesmo sem os pull-ups internos do ESP32, mas isso não determina resistência equivalente ou qualidade das transições. MicroPython e Espressif documentam o requisito de pull-up no I²C. [2][3]

## 4. Evidências diretas de comunicação

Na sequência mais recente em que o usuário confirmou o módulo do professor, foram registrados:

```text
LINHAS 1 SDA21 1 SCL22 1
LINHAS 2 SDA21 1 SCL22 1
LINHAS 3 SDA21 1 SCL22 1
SCAN ['0x76']
ENDERECO 0x76 ID 0x58
COINCIDE_REFERENCIA_PROFESSOR True
```

Esses resultados mostram acesso ao barramento e ao dispositivo. Não demonstram que o circuito de conversão inteiro esteja saudável. Nível alto em repouso também não certifica a integridade do sinal durante uma transação.

### 4.1 Coeficientes de calibração

Bloco de 24 bytes lido a partir de `0x88`:

```text
d46a7a633200b9946ed6d00bd513f9fff9ff8c3cf8c67017
```

Interpretação utilizada: `struct.unpack("<HhhHhhhhhhhh", dados)`.

| Coeficiente | Valor | Coeficiente | Valor |
| --- | ---: | --- | ---: |
| T1 | 27348 | P1 | 38073 |
| T2 | 25466 | P2 | −10642 |
| T3 | 50 | P3 | 3024 |
| P4 | 5077 | P5 | −7 |
| P6 | −7 | P7 | 15500 |
| P8 | −14600 | P9 | 6000 |

O bloco foi relido consistentemente e não era composto somente por zeros ou `FF`. Ele foi usado como referência entre trocas, sem garantia de unicidade como número de série. Nenhum coeficiente foi modificado para forçar uma temperatura desejada.

Coeficientes legíveis não certificam sua exatidão individual, a autenticidade do componente ou a integridade de sua conversão analógica. Os valores observados, isoladamente, não constituem prova de falsificação.

### 4.2 Últimas três amostras brutas registradas

Os seis bytes foram lidos a partir de `0xF7`; os três primeiros foram separados para pressão e os três seguintes para temperatura.

| Amostra | Bytes `F7..FC` | Pressão: três bytes | Temperatura: três bytes | ADC pressão | ADC temperatura |
| --- | --- | --- | --- | ---: | ---: |
| 1 | `611b70000000` | `61 1B 70` | `00 00 00` | 397751 | 0 |
| 2 | `611880000000` | `61 18 80` | `00 00 00` | 397704 | 0 |
| 3 | `6116a0000000` | `61 16 A0` | `00 00 00` | 397674 | 0 |

As contagens ADC não estão em °C, Pa ou hPa. A pressão bruta variou, mas isso não comprova uma pressão atmosférica compensada correta.

Também foram feitas consultas separadas a partir de `0xFA` e a cada byte térmico individual. O resultado continuou zerado, reduzindo a suspeita de erro apenas na separação dos seis bytes no programa.

## 5. Origem dos −132,7 °C

Esse número não descreve a temperatura real da casa. Ele é reproduzido ao aplicar a fórmula do programa original a `ADC_T = 0`, usando os coeficientes lidos do módulo:

```python
var1 = (adc_t / 16384.0 - T1 / 1024.0) * T2
var2 = (adc_t / 131072.0 - T1 / 8192.0) ** 2 * T3
t_fine = var1 + var2
temperatura_c = t_fine / 5120.0
```

Para `adc_t=0`, `T1=27348`, `T2=25466` e `T3=50`, a reprodução numérica fornece:

```text
var1          = −680121,2578125
var2          =      557,2386861
t_fine        = −679564,0191264
temperatura_c =     −132,7273475
```

A repetição do ADC zero explica a repetição de aproximadamente −132,7 °C. Não foi encontrada evidência de que o ambiente interno ou o tempo de estabilização produzissem esse valor. Acrescentar um deslocamento arbitrário esconderia a amostra inválida.

O driver atual rejeita o dado antes de publicá-lo. A mensagem registrada é:

```text
ValueError('Temperatura bruta invalida: 0x0',)
```

## 6. Consequência para a pressão

No cálculo do projeto, a pressão depende dos coeficientes `P1..P9`, da contagem bruta de pressão e de `t_fine`, obtido da temperatura. Assim, a pressão bruta pode mudar enquanto o resultado compensado continua inválido.

Durante etapas antigas, o cálculo com a temperatura incorreta produziu valores na ordem de 720 hPa. Esses números não foram aceitos como validação da pressão real. Altitude e comparação com barômetro de referência também não foram estabelecidas.

A Bosch descreve a calibração individual, a compensação térmica e o marcador de aquisição ignorada. A temperatura interna pode diferir da temperatura ambiente; utilizar o DHT22 em seu lugar seria uma aproximação experimental, não a restauração do funcionamento normal. [1]

Essa substituição não foi implementada. A pressão permanece ausente quando não pode ser validada.

## 7. Testes executados

| Ensaio | Procedimento | Resultado observado |
| --- | --- | --- |
| Endereço e ID | Scan e consulta em `0x76`/`0x77` | Módulo encontrado em `0x76`, ID `0x58`. |
| Calibração | Leitura de 24 bytes | Bloco legível e consistente com a referência registrada. |
| Frequência I²C | Leituras em 10, 50, 100 e 400 kHz durante etapas da sessão | Não recuperaram a temperatura. Parte dos ensaios consultou os registros disponíveis, sem uma conversão nova por frequência. |
| Reset | Escrita `0xB6` em `0xE0` e espera | Temperatura zero após nova configuração. |
| Inicialização e status | Espera da calibração e da aquisição, com limites | Nenhuma recuperação térmica observada. |
| Modo normal simples | `F4=0x27`, inicialmente com `F5=0xA0` | Temperatura zero. |
| Perfil equivalente aos defaults Adafruit | `F4=0xB7`, `F5=0x00` | Temperatura zero. |
| Modo forçado T×2/P×16 | `F4=0x55`, filtro desligado | Temperatura zero. |
| Temperatura isolada | Pressão desabilitada, temperatura ×1 e ×16 | Temperatura continuou zero; pressão apresentou marcador de aquisição ignorada. |
| Resoluções térmicas | ×1, ×2, ×4, ×8 e ×16 | Temperatura zero sem depender do driver do projeto na aquisição. |
| Temperatura desabilitada | Pressão habilitada, temperatura ignorada | Bytes térmicos `80 00 00`; ao habilitar, `00 00 00`. |
| Formas de transação | `readfrom_mem`, STOP separado e repeated START | Mesmo resultado térmico zero. |
| Bytes separados | Leitura de `FA`, `FB` e `FC` individualmente | Cada byte continuou zero. |
| Buffer de teste | Preenchimento prévio com `AA AA AA` e leitura para o mesmo buffer | Os bytes foram substituídos por `00 00 00`. |
| Medição contínua | Modo normal por 12 segundos sem reset entre amostras | Temperatura sempre zero; pressão bruta variável. |
| Wi-Fi desligado temporariamente | Leitura direta sem rádio ativo | Temperatura ainda zero; demais cargas físicas não foram isoladas. |
| Controles explícitos | CSB em 3V3 e SDO em GND, segundo montagem informada | Comunicação presente, sem temperatura utilizável. |
| Resistores de 4,7 kΩ | Pull-ups externos informados pelo usuário | Não houve recuperação nos testes posteriores; conexão não certificada por instrumento. |
| Mudança para SDA21/SCL22 | Nova pinagem, com LDR transferido para D18 | Comunicação confirmada e temperatura zero. |
| Configuração adicional enviada pelo usuário | T×2/P×16, filtro ×16, standby 500 ms; `F4=0x57`, `F5=0x90`, I²C 100 kHz | Valores `57/90` aceitos; seis consultas durante 12 segundos retornaram ADC térmico zero. |

As opções da configuração adicional foram conferidas na biblioteca oficial Adafruit e reproduzidas em MicroPython. Não foi executado um sketch Arduino compilado, nem foi substituído o firmware por Arduino ou CircuitPython. [4][5]

O retorno `80 00 00` corresponde ao ADC `0x80000`, marcador de aquisição ignorada. Ele é diferente do ADC zero quando a aquisição foi habilitada. Essa distinção está documentada pela Bosch. [1]

## 8. Hipóteses e limites das conclusões

| Hipótese | Relação com os dados | Verificação que ainda acrescentaria informação |
| --- | --- | --- |
| Anormalidade na aquisição térmica do módulo | Compatível com comando aceito e ADC térmico zero em modos diferentes | Teste cruzado com placa e módulo de funcionamento conhecido. |
| Alimentação inadequada no ponto do módulo | Comunicação digital não caracteriza toda a alimentação durante conversão | Medir VCC/GND sob carga e, se necessário, os transientes. |
| Soldas, jumpers ou protoboard | Houve trocas e conectores soldados em lados diferentes | Inspeção e continuidade com circuito desenergizado. |
| Integridade dos sinais I²C | Leituras são consistentes, mas não há oscilograma | Conferir pull-ups efetivos, bordas, níveis e transações. |
| Particularidade de inicialização/compatibilidade | Diversas configurações não resolveram, reduzindo essa suspeita | Comparar outra implementação ou outra placa usando o mesmo módulo. |
| Endereço errado | Pouco compatível com ID e coeficientes repetidamente lidos em `0x76` | Reconfirmar após mudança de SDO ou troca física de módulo. |
| Simples desvio de temperatura ambiente | Não explica, por si só, registradores sempre zerados | Primeiro obter amostra válida; depois comparar com referência. |

Não foram comprovados: sensor definitivamente queimado, curto direto entre pinos, solda aberta específica, alimentação correta em todos os instantes ou defeito igual nos três módulos. Também não foi demonstrada autenticidade ou falsificação do componente.

Uma linha baixa não identifica sozinha a causa física. Um GPIO que sobe quando isolado também não tem, por esse único ensaio, todas as suas características elétricas certificadas.

## 9. Correções aplicadas ao projeto

O firmware foi atualizado para:

- Usar explicitamente LDR18, DHT22 no D4, MQ-135 no D34 e BMP280 em SDA21/SCL22.
- Comunicar por `SoftI2C` a 50 kHz, com timeout de espera de clock stretching configurado em 5 ms. Esse parâmetro não limita, sozinho, a duração total de toda sequência de transações. [2]
- Reiniciar o BMP280 e aguardar a disponibilização dos coeficientes.
- Realizar aquisição forçada T×2/P×16 e esperar o fim da conversão, com limite de um segundo.
- Rejeitar calibração inválida, contagens zero/ignoradas/saturadas e resultados fora dos limites físicos adotados.
- Retornar campos BMP nulos em falha e tentar novamente após cinco segundos.
- Manter os demais sensores enviando dados; foram preservadas cópias dos arquivos anteriores da placa.

Essas medidas corrigiram a pinagem e o tratamento de erros. Não recuperaram a conversão térmica do módulo nos ensaios realizados.

### 9.1 Representação correta de ausência de medição

```json
{
  "pressao": null,
  "temperatura_bmp": null,
  "bmp_conectado": false
}
```

`null` não é zero: significa que o programa não disponibilizou uma medição válida. O SQLite armazena `NULL`, e o painel mostra ausência de leitura.

No código atual, `bmp_conectado=false` indica que não há medição BMP validada. O dispositivo pode estar presente no I²C e ainda produzir esse indicador falso. Por isso, a mensagem do painel foi alterada para “Sem medição válida”.

A API do projeto admite temperatura BMP entre −40 e 85 °C. Um payload com −132,7 °C seria rejeitado com HTTP 422. A rejeição prévia no driver evita que a falha comprometa a gravação do lote inteiro.

## 10. Evidências de que a estação continua operando

Após reiniciar o firmware, os IDs de leitura avançaram de `1862` para `1863`. O registro 1863 apresentava:

| Campo | Valor |
| --- | --- |
| Estação | `esp32-01` |
| Temperatura DHT22 | 21,4 °C |
| Umidade DHT22 | 77,2% |
| LDR | 1 / Escuro |
| MQ-135 | 107, valor bruto ADC |
| Pressão BMP | `null` |
| Temperatura BMP | `null` |
| Indicador BMP | `false` |
| Horário UTC | `2026-11-11T03:00:26.621231+00:00` |
| Mesmo instante em UTC−3 | 11/11/2026, 00:00:26 |

Durante a elaboração, também foi consultado o registro 1878, recebido às `03:01:49 UTC`, ou `00:01:49` no fuso de referência. Ele continuava com BMP nulo e campos dos outros sensores preenchidos.

Esses dados comprovam novas recepções e gravações naquelas verificações. O MQ-135 não foi calibrado para ppm. Uma leitura estática do LDR não certifica sua reação à mudança de iluminação.

### 10.1 Testes de software

A última suíte executada após a atualização de pinagem apresentou **14 testes aprovados**, incluindo compensação numérica, rejeição de ADC térmico inválido, calibração zerada, timeout, recuperação simulada, autenticação, persistência e aceite de payload com BMP nulo e outros sensores válidos.

Um vetor numérico de teste, com seus próprios coeficientes e ADCs `519888`/`415148`, produz aproximadamente 25,08 °C e 1006,53 hPa. Esses coeficientes não substituem os do módulo real.

Também foram verificados integridade da entrega ZIP, preservação do HTML e exclusão das configurações privadas. Esses testes validam o software, não o componente físico, suas soldas ou a precisão dos sensores.

## 11. Separação dos outros dois módulos

| Módulo | Observação registrada | O que não foi comprovado |
| --- | --- | --- |
| Professor | ID `0x58`, endereço `0x76`, coeficientes legíveis e ADC térmico zero | Causa física da temperatura inválida. |
| Associado à etiqueta B/segundo | Uma leitura plausível de 23,3 °C/938,12 hPa, seguida de perda de comunicação; SCL baixo em testes posteriores | Estabilidade, precisão e origem exata do nível baixo. |
| Associado à etiqueta A/terceiro | Não detectado nos testes registrados, mesmo com linhas altas em repouso | Que esteja desligado, queimado ou com solda defeituosa. |

As etiquetas e a correspondência dos módulos foram organizadas com o usuário. Sem identificação individual dos dois restantes, comportamento isolado não fornece reconhecimento eletrônico infalível.

Os testes com SCL baixo e retirada temporária de CSB/SDO em outra montagem não foram usados como prova de defeito térmico do módulo do professor.

## 12. Próximos passos que realmente acrescentam informação

Não é necessário desmontar toda a estação para continuar investigando. Recomenda-se:

1. Manter etiqueta e fotos dos dois lados do módulo do professor, incluindo os pontos de solda.
2. Medir VCC/GND diretamente no módulo durante a operação. A origem do fio em 3V3 não substitui essa medição.
3. Inspecionar os conectores e verificar continuidade desenergizada. Um aviso sonoro isolado do multímetro precisa ser interpretado considerando o circuito, não automaticamente como curto.
4. Conferir fisicamente SDA21/SCL22, GND comum e as ligações dos pull-ups antes de acrescentar resistores.
5. Comparar este módulo em outra placa comprovadamente funcional e um módulo estável na montagem atual. Um exemplo independente pode ser usado; o código original do professor não é indispensável.
6. Se houver equipamento disponível, observar o I²C com analisador lógico ou osciloscópio.
7. Considerar a recuperação comprovada somente após várias temperaturas internas plausíveis, pressão compensada validada e novos campos BMP não nulos no banco.

Enquanto a investigação estiver pendente, é adequado manter os demais sensores registrando e o BMP explicitamente sem medição válida. Não se deve apresentar como pressão real um resultado compensado com ADC térmico zero.

## 13. Reprodução do teste por USB

Na raiz do projeto, com a porta serial livre e ajustando COM5 se necessário:

```powershell
.\.venv\Scripts\python.exe -m mpremote connect list
.\.venv\Scripts\python.exe -m mpremote connect COM5 soft-reset run scripts/diagnosticar_bmp280.py
.\.venv\Scripts\python.exe -m mpremote connect COM5 reset
```

O script usa SDA21/SCL22, consulta identificação e calibração, mantém aquisição normal por aproximadamente 12 segundos e compara leituras térmicas. A coleta normal fica pausada durante o diagnóstico; o reset final a retoma.

Para verificar o software:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Arquivos relevantes: `firmware/main.py`, `firmware/sensors/bmp280.py`, `backend/schemas.py`, `tests/test_bmp280.py` e `scripts/diagnosticar_bmp280.py`.

## 14. Conclusão técnica

O módulo do professor apresenta **comunicação I²C observável e temperatura bruta persistentemente zerada**. O resultado foi obtido diretamente dos registradores, em transações e configurações diferentes, antes da API e do painel.

Os −132,7 °C foram explicados pelo cálculo sobre esse zero e não representam uma temperatura medida. A pressão bruta varia, mas a pressão compensada permanece sem validação térmica.

O firmware atualizado limita esperas, corrige os pinos e evita publicar dados inválidos. A estação demonstrou continuidade de recepção e gravação dos demais sensores. **A pendência é identificar a causa da aquisição térmica inválida ou comprovar sua recuperação; módulo, alimentação e interconexões continuam como possibilidades não encerradas.**

## Referências

[1] Bosch Sensortec. [BMP280 — Data sheet](https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bmp280-ds001.pdf), revisão 1.26, outubro de 2021. Seções 3.3, 3.11, 4.3 e 6.3.

[2] MicroPython. [class I2C — a two-wire serial protocol](https://docs.micropython.org/en/latest/library/machine.I2C.html). Métodos de leitura e pull-up.

[3] Espressif Systems. [Inter-Integrated Circuit — ESP-IDF Programming Guide](https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/peripherals/i2c.html). Características do barramento e pull-ups.

[4] Adafruit. [Adafruit_BMP280_Library — implementação](https://github.com/adafruit/Adafruit_BMP280_Library/blob/master/Adafruit_BMP280.cpp).

[5] Adafruit. [Adafruit_BMP280_Library — opções de configuração](https://github.com/adafruit/Adafruit_BMP280_Library/blob/master/Adafruit_BMP280.h).

As páginas latest/master podem mudar. As conclusões deste documento se referem às observações registradas na sessão, não a uma certificação do componente físico.
