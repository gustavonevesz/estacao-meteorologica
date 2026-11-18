#include <Wire.h>
#include <Adafruit_BMP280.h>
#include <math.h>

// Diagnostico temporario: nao configura Wi-Fi nem os demais sensores.
// Biblioteca de referencia: Adafruit BMP280 Library 3.0.0.
constexpr int SDA_BMP = 21;
constexpr int SCL_BMP = 22;
constexpr uint32_t INTERVALO_LEITURA_MS = 1000;
constexpr uint32_t INTERVALO_TENTATIVA_MS = 5000;

Adafruit_BMP280 bmp;
bool sensorPronto = false;
uint8_t enderecoAtivo = 0;
uint32_t ultimaTentativa = 0;
uint32_t ultimaLeitura = 0;
uint32_t amostrasValidas = 0;
uint32_t amostrasInvalidas = 0;

bool lerRegistradores(uint8_t endereco, uint8_t registro, uint8_t *destino,
                      size_t tamanho) {
  Wire.beginTransmission(endereco);
  if (Wire.write(registro) != 1) {
    Wire.endTransmission(true);
    Serial.println("ERRO: nao foi possivel preparar o endereco do registrador");
    return false;
  }
  const uint8_t erro = Wire.endTransmission(false);
  if (erro != 0) {
    Serial.printf("ERRO_I2C endereco=0x%02X registro=0x%02X codigo=%u\n",
                  static_cast<unsigned>(endereco),
                  static_cast<unsigned>(registro), static_cast<unsigned>(erro));
    return false;
  }
  const size_t recebidos = Wire.requestFrom(endereco, tamanho, true);
  if (recebidos != tamanho) {
    Serial.printf("ERRO_I2C registro=0x%02X esperado=%u recebido=%u\n",
                  static_cast<unsigned>(registro),
                  static_cast<unsigned>(tamanho),
                  static_cast<unsigned>(recebidos));
    while (Wire.available()) {
      Wire.read();
    }
    return false;
  }
  for (size_t i = 0; i < tamanho; ++i) {
    const int valor = Wire.read();
    if (valor < 0) {
      Serial.println("ERRO_I2C: faltou byte na resposta");
      return false;
    }
    destino[i] = static_cast<uint8_t>(valor);
  }
  return true;
}

void imprimirHex(const uint8_t *dados, size_t tamanho) {
  for (size_t i = 0; i < tamanho; ++i) {
    Serial.printf("%02X", static_cast<unsigned>(dados[i]));
  }
}

void imprimirBloco(const char *nome, uint8_t endereco, uint8_t registro,
                   size_t tamanho) {
  uint8_t dados[24];
  if (tamanho > sizeof(dados)) {
    Serial.println("ERRO: bloco de diagnostico maior que o buffer");
    return;
  }
  Serial.printf("%s=", nome);
  if (!lerRegistradores(endereco, registro, dados, tamanho)) {
    Serial.println("INDISPONIVEL");
    return;
  }
  imprimirHex(dados, tamanho);
  Serial.println();
}

bool inicializarSensor() {
  const uint8_t candidatos[] = {0x76, 0x77};
  for (uint8_t endereco : candidatos) {
    Serial.printf("\nINICIO t_ms=%lu endereco=0x%02X\n",
                  static_cast<unsigned long>(millis()),
                  static_cast<unsigned>(endereco));
    // Captura anterior a begin(): permite ver o que a biblioteca modifica.
    uint8_t identidade;
    if (!lerRegistradores(endereco, 0xD0, &identidade, 1)) {
      Serial.println("ID_ANTES=INDISPONIVEL");
      continue;
    }
    Serial.printf("ID_ANTES=0x%02X\n", static_cast<unsigned>(identidade));
    uint8_t calibracao[24];
    if (!lerRegistradores(endereco, 0x88, calibracao, sizeof(calibracao))) {
      Serial.println("CAL_ANTES_88_9F=INDISPONIVEL");
      continue;
    }
    Serial.print("CAL_ANTES_88_9F=");
    imprimirHex(calibracao, sizeof(calibracao));
    Serial.println();
    bool todosZero = true;
    bool todosFF = true;
    for (uint8_t valor : calibracao) {
      todosZero = todosZero && valor == 0;
      todosFF = todosFF && valor == 0xFF;
    }
    const uint16_t t1 = calibracao[0] | (static_cast<uint16_t>(calibracao[1]) << 8);
    const uint16_t p1 = calibracao[6] | (static_cast<uint16_t>(calibracao[7]) << 8);
    if (todosZero || todosFF || t1 == 0 || p1 == 0) {
      Serial.println("CALIBRACAO_INVALIDA: inicializacao cancelada");
      continue;
    }
    imprimirBloco("STATUS_CTRL_CONFIG_ANTES_F3_F5", endereco, 0xF3, 3);
    imprimirBloco("RAW_ANTES_F7_FC", endereco, 0xF7, 6);
    if (identidade != 0x58) {
      Serial.println("ID diferente de BMP280; configuracao nao aplicada");
      continue;
    }
    if (!bmp.begin(endereco)) {
      Serial.println("ADAFRUIT_BEGIN=FALHOU");
      continue;
    }
    // Mantem os defaults oficiais durante todo o teste, sem setSampling().
    enderecoAtivo = endereco;
    Serial.printf("ADAFRUIT_BEGIN=OK ID=0x%02X\n",
                  static_cast<unsigned>(bmp.sensorID()));
    imprimirBloco("STATUS_CTRL_CONFIG_DEPOIS_F3_F5", endereco, 0xF3, 3);
    return true;
  }
  Serial.println("Sem BMP280 inicializado; nova tentativa em 5 segundos");
  return false;
}

uint32_t adc20(const uint8_t *dados) {
  return (static_cast<uint32_t>(dados[0]) << 12) |
         (static_cast<uint32_t>(dados[1]) << 4) |
         (static_cast<uint32_t>(dados[2]) >> 4);
}

bool adcUtilizavel(uint32_t valor) {
  // Zero e todos os bits em 1 sao rejeitados defensivamente neste teste.
  // 0x80000 e o valor documentado para medicao ignorada.
  return valor != 0 && valor != 0x80000 && valor != 0xFFFFF;
}

void setup() {
  Serial.begin(115200);
  delay(1500);
  Serial.println("\nDIAGNOSTICO TEMPORARIO BMP280 / ADAFRUIT 3.0.0");
  Serial.printf("SDA=%d SCL=%d I2C=100000Hz timeout=50ms\n", SDA_BMP, SCL_BMP);
  Wire.begin(SDA_BMP, SCL_BMP, 100000);
  Wire.setTimeOut(50);
  ultimaTentativa = millis();
  sensorPronto = inicializarSensor();
}

void loop() {
  const uint32_t agora = millis();
  if (!sensorPronto) {
    if (static_cast<uint32_t>(agora - ultimaTentativa) >= INTERVALO_TENTATIVA_MS) {
      ultimaTentativa = agora;
      sensorPronto = inicializarSensor();
    }
    delay(10);
    return;
  }
  if (static_cast<uint32_t>(agora - ultimaLeitura) < INTERVALO_LEITURA_MS) {
    delay(5);
    return;
  }
  ultimaLeitura = agora;

  uint8_t bruto[6];
  uint8_t controle[3];
  if (!lerRegistradores(enderecoAtivo, 0xF7, bruto, sizeof(bruto)) ||
      !lerRegistradores(enderecoAtivo, 0xF3, controle, sizeof(controle))) {
    ++amostrasInvalidas;
    sensorPronto = false;
    ultimaTentativa = millis();
    Serial.println("AMOSTRA_INVALIDA: resposta I2C incompleta; reconexao em 5s");
    return;
  }
  const uint32_t adcPressao = adc20(bruto);
  const uint32_t adcTemperatura = adc20(bruto + 3);
  const float temperatura = bmp.readTemperature();
  const float pressao = bmp.readPressure() / 100.0f;
  const bool valida = adcUtilizavel(adcTemperatura) && adcUtilizavel(adcPressao) &&
                      isfinite(temperatura) && isfinite(pressao) &&
                      temperatura >= -40.0f && temperatura <= 85.0f &&
                      pressao >= 300.0f && pressao <= 1100.0f;
  if (valida) {
    ++amostrasValidas;
  } else {
    ++amostrasInvalidas;
  }

  Serial.printf("t_ms=%lu addr=0x%02X RAW6=",
                static_cast<unsigned long>(millis()),
                static_cast<unsigned>(enderecoAtivo));
  imprimirHex(bruto, sizeof(bruto));
  Serial.printf(" ADC_P=%lu ADC_T=%lu F3_F4_F5=",
                static_cast<unsigned long>(adcPressao),
                static_cast<unsigned long>(adcTemperatura));
  imprimirHex(controle, sizeof(controle));
  Serial.printf(" T=%.3fC P=%.3fhPa PLAUSIVEL=%s total_plausiveis=%lu invalidas=%lu\n",
                temperatura, pressao, valida ? "SIM" : "NAO",
                static_cast<unsigned long>(amostrasValidas),
                static_cast<unsigned long>(amostrasInvalidas));
}
