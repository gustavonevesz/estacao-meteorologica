# Gravação da demonstração — Estação Meteorológica

Roteiro adaptado ao sistema existente em 12/11/2026. Os três blocos abaixo ocupam 4min30s, entre 2:30 e 7:00 de um vídeo maior. Grave três trechos de aproximadamente 90 segundos; os tempos indicam a posição na edição final.

## O que será demonstrado

```text
Sensores → ESP32/MicroPython → Wi-Fi → HTTP POST com JSON
         → FastAPI/Pydantic → SQLite → painel HTML/CSS/JavaScript
```

| Item do roteiro inicial | Demonstração desta versão |
| --- | --- |
| MQTT e subscriber | HTTP POST e rota de recepção do FastAPI |
| Exclusão de outliers e médias móveis | Validação de tipos, faixas e consistência; não há média móvel |
| Banco relacional | SQLite, tabela `leituras`, INSERT e SELECT parametrizados |
| Mapa e coordenadas | Não implementados; citar como evolução, se necessário |
| Gráficos históricos | Histórico real em tabela e exportação CSV |
| Alertas extremos | Estado da API, atraso de dados e ausência de medição válida; não há alerta de temperatura extrema |

Não chamar HTTP de MQTT, tabela de gráfico nem validação por faixa de média móvel. Uma leitura anterior exibida no banco não comprova transmissão atual: mostre horário recente e IDs aumentando.

## Preparação

Pasta do projeto: `C:\Users\Windows\computer-science\estacao-meteorologica`.

1. Ligue o ESP32 e conecte computador e placa à rede configurada. O firmware usa o IP do notebook em `API_URL`; uma mudança de rede pode exigir atualizá-lo na placa.
2. Abra o atalho **Estação Meteorológica** na Área de Trabalho. Ele inicia a API e abre `http://127.0.0.1:8000/`. Mantenha o console do servidor aberto.
3. Confirme o estado **Recebendo dados**, horário recente e novos registros. Se aparecer **Sem leituras recentes**, ainda não comece a gravação como demonstração ao vivo.
4. Para o bloco do Thonny, conecte a placa por USB de dados. A alimentação pela tomada permite enviar por Wi-Fi, mas não dá acesso ao console USB do Thonny. Feche outros monitores seriais antes de abrir a porta no Thonny.
5. No Thonny, selecione **MicroPython (ESP32)** e a porta real da placa. Abra o arquivo principal da placa para exibir o código efetivamente em execução. Não execute o firmware com o interpretador Python do computador.
6. A cópia local de `firmware/main.py` ganhou logs para a gravação. Eles só aparecerão depois de transferir esse arquivo à placa e reiniciá-la. Preserve uma cópia do `main.py` atual da placa antes da transferência. Não é necessário trocar o MicroPython, gravar Arduino nem alterar os drivers dos sensores.
7. No VS Code, deixe abertos `backend/main.py`, `backend/schemas.py` e `backend/database.py`. Não abra `.env` ou `firmware/config.py` durante a gravação.
8. Abra outro terminal PowerShell na raiz do projeto e execute:

```powershell
.\.venv\Scripts\python.exe -u scripts\acompanhar_banco.py
```

O monitor usa `mode=ro` e `PRAGMA query_only`: não insere, modifica nem apaga medições. Ele identifica as linhas antigas como `[HISTORICO]` e somente inserções vistas depois da abertura como `[NOVO INSERT]`. `Ctrl+C` encerra a consulta sem desligar o servidor.

No VS Code, também é possível usar **Terminal → Executar Tarefa → Gravação: acompanhar inserções no SQLite**, sem digitar o comando.

Para uma consulta única com o registro completo em JSON:

```powershell
.\.venv\Scripts\python.exe scripts\acompanhar_banco.py --uma-vez --json
```

## Bloco 3 — 2:30 a 4:00 | Firmware e transmissão HTTP

### 2:30–3:00 — código principal

**Na tela:** Thonny com `main.py`, a lista de quatro sensores e o laço `while True`. Aumente a fonte para que os pinos e `dados.update(leitura)` fiquem legíveis.

**Narração:**

> O ESP32 executa MicroPython e reúne quatro sensores: luminosidade, temperatura e umidade, gás e pressão atmosférica. Cada sensor tem seu próprio arquivo. O programa principal chama os drivers e combina os resultados em um dicionário identificado como esp32-01. A organização permite testar e corrigir cada módulo separadamente. Se uma medição falhar, ela pode aparecer como ausente, em vez de inventarmos um valor para preencher o painel.

### 3:00–3:30 — leituras e payload

**Na tela:** console mostrando um ciclo real com `[SENSOR]` e `[PAYLOAD JSON]`. Mostre a temperatura, a umidade e a pressão que realmente aparecerem; não decore números fixos.

**Narração:**

> No console vemos a saída de cada sensor e o payload JSON montado para transmissão. As temperaturas são expressas em graus Celsius, a umidade em porcentagem e a pressão em hectopascais. A luminosidade é digital, e o MQ-135 fornece um valor bruto do conversor analógico, não uma concentração calibrada em ppm. O JSON mantém os campos e unidades esperados pelo backend.

### 3:30–4:00 — Wi-Fi e confirmação de envio

**Na tela:** `[WIFI] Conectado | IP: ...`, seguido de `[HTTP] 201 Created`. Selecione a chamada `enviar(...)` e, se couber, `ujson.dumps(dados)` em `api_client.py`.

**Narração:**

> A placa verifica a conexão Wi-Fi e envia o JSON por HTTP POST para a API local. Nesta implementação usamos HTTP, com uma chave no cabeçalho da requisição. A chave não aparece nos logs da demonstração. O status 201 confirma que a API aceitou e salvou a leitura. Esse fluxo se repete em ciclos; o console do servidor também permite acompanhar a chegada das requisições.

## Bloco 4 — 4:00 a 5:30 | Backend e persistência

### 4:00–4:30 — recepção e validação

**Na tela:** `backend/main.py`, rota `POST /api/leituras`; depois `backend/schemas.py`, limites e `validar_estados`.

**Narração:**

> O backend utiliza FastAPI. A rota de recepção verifica a chave de acesso e recebe os dados em um modelo Pydantic. Esse modelo valida os tipos, os intervalos físicos definidos e a consistência dos campos. Por exemplo, a umidade precisa estar entre zero e cem por cento, e um BMP280 sem medição válida deve informar pressão e temperatura nulas. Uma requisição inválida é rejeitada, em vez de ser gravada silenciosamente como uma leitura correta.

### 4:30–5:00 — INSERT e confirmação

**Na tela:** `backend/database.py`, `CREATE TABLE` e `salvar`; console com `SQL INSERT confirmado`, ID e payload. Mostre também o status HTTP 201.

**Narração:**

> Depois da validação, a classe Banco faz um INSERT parametrizado no SQLite. O banco atribui um identificador ao registro, e o backend acrescenta o horário de recebimento em UTC. A transação é confirmada antes de a API responder com sucesso. Os dados ficam em disco, no arquivo estacao.db, e continuam disponíveis quando fechamos o navegador ou reiniciamos o servidor. Esta versão preserva as medições recebidas; ainda não aplica médias móveis.

### 5:00–5:30 — consulta real

**Na tela:** terminal com `scripts/acompanhar_banco.py`, SQL SELECT e pelo menos dois `[NOVO INSERT]` com IDs crescentes. Se não chegarem registros, interrompa o ensaio para resolver a conexão.

**Narração:**

> Aqui consultamos diretamente a tabela leituras em modo somente leitura. O terminal distingue o histórico inicial das novas inserções. Os IDs e os horários permitem relacionar o envio da placa com a persistência no banco. Essa consulta verifica o que está salvo de fato, independentemente do painel web. A consulta é parametrizada e não altera o banco durante a demonstração.

## Bloco 5 — 5:30 a 7:00 | Painel e conclusões

### 5:30–6:00 — dados atuais

**Na tela:** navegador com `http://127.0.0.1:8000/`, seis cartões, estado **Recebendo dados** e horário da última leitura.

**Narração:**

> O frontend reúne as medições em um painel no navegador. Ele consulta a API a cada cinco segundos e apresenta temperatura, umidade, pressão, luminosidade, sinal do sensor de gás e temperatura do BMP280. O horário de recebimento ajuda a confirmar a atualização. A interface informa quando não há leitura recente ou quando um sensor está sem medição válida.

### 6:00–6:30 — histórico e exportação

**Na tela:** role até a tabela, mostre os últimos registros e clique em **Exportar CSV**. A tabela e o download são recursos reais; não é necessário editar os dados.

**Narração:**

> Na tabela podemos comparar as últimas cem leituras e exportar o histórico visível em CSV para análise. O conteúdo é recuperado do banco relacional, portanto não depende de manter esta aba aberta durante a coleta. Esta versão apresenta o histórico em tabela. Mapas geográficos, gráficos e alertas para condições extremas são possibilidades de evolução e não fazem parte desta demonstração.

### 6:30–7:00 — limitações e próximos passos

**Na tela:** painel e, se disponível, uma imagem ou filmagem real da montagem. Não use uma imagem genérica como evidência da placa montada.

**Narração:**

> O protótipo demonstrou a integração entre sensores, firmware, transmissão, banco e interface. A montagem em protoboard ainda depende da qualidade dos contatos e não é adequada para exposição ao tempo. Os próximos passos incluem uma placa de circuito impresso, revisão da alimentação, calibração dos sensores e um invólucro apropriado, com estudo de proteção IP65. O abrigo deve permitir ventilação e medição representativa, sem simplesmente vedar os sensores. Também podemos evoluir o software com gráficos, localização e alertas.

## Como capturar os três trechos

Neste notebook está instalada a Ferramenta de Captura do Windows. Pressione **Win + Shift + R**, selecione a área e inicie a gravação. Confira o microfone antes de gravar a narração. A [documentação da Microsoft](https://support.microsoft.com/en-us/windows/apps/use-snipping-tool-to-capture-screenshots) descreve esse modo de captura.

Grave um teste curto e assista para conferir fonte legível, áudio e se o console está dentro da área capturada. Depois grave cada bloco separadamente, nomeando os arquivos `bloco_3_firmware.mp4`, `bloco_4_backend_banco.mp4` e `bloco_5_painel.mp4`. Os nomes são sugestões; ainda não são vídeos produzidos.

Use uma região ampla o suficiente para alternar entre editor, terminal e navegador. Não grave senhas, chaves ou notificações pessoais. Se quiser gravar sem narração, faça a fala depois durante a edição.

## Critério para começar a gravação final

- Console USB do Thonny recebendo ciclos reais para o bloco 3.
- Log de payload JSON e conexão Wi-Fi na placa, depois de atualizar `main.py`.
- API respondendo e confirmando inserções reais.
- Consulta SQL mostrando novos IDs, não apenas os registros históricos.
- Painel com horário atual e estado **Recebendo dados**.
- Texto de narração ajustado ao que ocorreu no ensaio; falha ou dado ausente não deve ser apresentado como sucesso.

Os logs novos foram preparados no computador. A atualização da placa e a gravação final dependem de conectá-la por USB; editar os arquivos locais não altera automaticamente o firmware em execução.
