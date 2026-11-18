# Diagnostico temporario do BMP280 com Arduino e Adafruit

Este sketch compara o comportamento do modulo com a biblioteca oficial
**Adafruit BMP280 Library 3.0.0**, mantendo seus parametros padrao durante todo
o teste. Nao muda o modo de amostragem apos um periodo de tempo.

Configuracao: ESP32 Dev Module (`esp32:esp32:esp32`), Arduino-ESP32 2.0.17 ou 3.3.12,
SDA GPIO21, SCL GPIO22, I2C 100 kHz e serial 115200 baud. O codigo tenta os
enderecos `0x76` e `0x77` e exige identificacao `0x58` antes de inicializar.

**Antes de gravar este sketch, e obrigatorio salvar e verificar um backup
completo da flash do ESP32 com esptool.** O programa Arduino substitui
temporariamente o MicroPython e pode sobrescrever as particoes existentes.
Uma copia somente dos arquivos `.py` nao substitui o backup da flash.

O codigo nao usa Wi-Fi nem configura os pinos dos demais sensores. Durante
o teste, o firmware da estacao nao executa e novas leituras deixam de ser
enviadas a API. O banco de dados no computador permanece independente.

O log mostra identificacao, 24 bytes de calibracao, estado/controle/configuracao
e os dados brutos antes de `begin()`. Em seguida, registra uma amostra por
segundo, com dados brutos, temperatura e pressao calculadas pela Adafruit,
indicador de plausibilidade e contadores. As leituras diagnosticas proprias
informam erros de transmissao e respostas incompletas explicitamente; bytes
ausentes nao viram zeros. O bloco de calibracao proprio e rejeitado se estiver
todo em zero/FF ou com T1/P1 zerados. Isso nao modifica a biblioteca Adafruit.

A conversao da biblioteca e o bloco bruto usam transacoes distintas. No modo
normal, podem representar amostras consecutivas, em vez da mesma aquisicao
exata. Leituras zero, ignoradas (`0x80000`), saturadas (`0xFFFFF`), nao finitas
ou fora de -40 a 85 graus Celsius / 300 a 1100 hPa sao marcadas invalidas.
As leituras internas da Adafruit usam transacoes separadas e nao expoem todos
os erros de transporte. Esse indicador nao certifica integridade de todas as
transacoes, autenticidade, calibracao ou precisao do modulo.
Erros de inicializacao/comunicacao permitem nova tentativa a cada 5 segundos.

**A restauracao nao e automatica:** depois de capturar o log, restaurar o
backup completo da flash usando esptool e verificar que o MicroPython voltou
a iniciar, que os arquivos/configuracoes foram preservados e que a API recebe
novas leituras. Utilizar a porta, o tamanho de flash e o arquivo de backup
realmente verificados para essa placa. Nao executar `erase-flash` como rotina
de diagnostico.

Fontes: [biblioteca Adafruit](https://github.com/adafruit/Adafruit_BMP280_Library)
e [Arduino-ESP32](https://docs.espressif.com/projects/arduino-esp32/en/latest/).
