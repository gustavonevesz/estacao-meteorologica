# Registro de alterações

## 2026-11-11 — Rosa dos ventos

- Novo ícone de oito pontas, sem letras e com fundo transparente, usando
  branco e o verde petróleo `#183B38` do painel, no atalho e no favicon.

## 2026-11-11 — Projeto movido para computer-science

- Projeto transferido para `C:\Users\Windows\computer-science\estacao-meteorologica`, com banco, configurações e backups preservados.
- Conferidos 153 arquivos antes dos ajustes de caminho e a integridade do banco com 4174 registros no fim da transferência.
- Ambiente `.venv` recriado no destino com as 40 versões de pacotes anteriormente instaladas; ambiente antigo preservado em `.tools/migracao_pasta_20261111_190800/`.
- Atalho atualizado e usado para iniciar o servidor no novo local.
- Tempo de verificação HTTP do iniciador ajustado para 3 s: o Windows levou cerca de 2 s para informar conexão recusada quando a API estava desligada.

## 2026-11-11 — Ícone branco

- Símbolo do navegador alterado para branco sólido, com fundo e recortes
  transparentes, no vetor, ICO do atalho e favicon do painel.

## 2026-11-11 — Painel direto do ESP32

- Removidos o campo Estação e o botão Atualizar; o painel consulta diretamente
  `esp32-01` e mantém a atualização automática a cada cinco segundos.
- Histórico, cartões e exportação CSV continuam usando somente a estação real.
  Demonstração com `simulador` permanece separada e consultável pela API.
- Guia de execução e diagnóstico atualizados para a interface sem seletor.

## 2026-11-11 — Ícone verde de navegador

- Ícone redesenhado com curvas de navegador inspiradas no Edge, usando a
  paleta verde petróleo do painel, em SVG, PNG e ICO com transparência.
- Mesmo desenho usado como favicon da aba do painel.
- Instalador usa uma cópia do ICO com hash no nome para atualizar a aparência
  no Windows sem apagar caches do sistema nem reiniciar o Explorer.
- Inicialização do servidor e firmware permanecem com o comportamento anterior.

## 2026-11-11 — Atalho Estação Meteorológica no Windows

- Criado iniciador que reconhece a API já ativa, inicia um console do FastAPI
  quando necessário, espera a API responder e abre o navegador padrão.
- Cliques simultâneos são serializados com mutex; outro serviço na porta 8000
  é preservado. O iniciador não troca de porta nem altera o ESP32.
- Adicionados instalador do atalho, vetor SVG, prévia PNG e ICO transparente
  com sete tamanhos. Arquivos e guia `ATALHO_WINDOWS.md` incluídos no ZIP.
- Testada a abertura pelo atalho real: servidor na porta 8000 manteve o PID.
  Partida em porta e banco temporários confirmou painel, POST e persistência;
  somente o processo temporário criado pelo teste foi encerrado.
- Conjunto completo: 46 testes passaram. Nenhuma mudança de firmware,
  credencial, firewall ou configuração Wi-Fi foi necessária.

## 2026-11-11 — Referência após recuperar as leituras BMP280

- Preservados 217 registros válidos consecutivos, IDs 3443–3659, recebidos entre
  14:20:17 e 14:40:03 (UTC−3), e as amostras brutas dos monitores válido/inválidos.
- Criado `RELATORIO_FUNCIONAMENTO_E_RECUPERACAO_BMP280.md`, com montagem,
  calibração comparada, parâmetros do driver e procedimento de diagnóstico.
- Evidências públicas, fontes de referência e manifesto SHA-256 guardados em
  `diagnosticos/referencia_bmp280_20261111/`, sem credenciais ou imagens de flash.
- Identificação do segundo módulo tratada como contextual. A aquisição já havia
  voltado no programa normal antes do monitor temporário; a causa física exata
  da recuperação não foi comprovada.
- Relatório e evidências incluídos nas próximas entregas do empacotador.
  Dois testes de empacotamento passaram. Nenhuma nova operação serial ou gravação
  de firmware foi necessária para elaborar o relatório.

## 2026-11-10 — Pinagem definitiva LDR18 e BMP21/22

- Usuário confirmou que o sensor transferido para D18 é o LDR.
- LDR passa a GPIO18 e BMP280 a SDA GPIO21/SCL GPIO22, com pinagem explícita
  no main e defaults coerentes nos drivers. DHT22 permanece em GPIO4 e MQ em GPIO34.
- DHT22 testado diretamente com duas leituras válidas no GPIO4.
- Diagnóstico independente e instruções atualizados para a nova montagem.
- Firmware enviado após backup; serial confirmou salvamento na API e registros
  consecutivos no banco. DHT22 mediu 20,5 °C/76,2%, MQ-135 110 e LDR foi lido
  como escuro na validação. A variação do LDR com luz ainda depende de teste físico.
- Painel informa "Sem medição válida" quando o BMP falha, pois ele pode estar
  detectado mesmo sem conseguir entregar uma leitura utilizável.
- BMP do professor continua respondendo com ID 0x58 em 0x76, mas temperatura
  bruta zero, inclusive no perfil equivalente ao sketch enviado pelo usuário.

## 2026-11-10 — Entrega por ZIP e testes com montagem intacta

- Confirmada a reconexão à rede do iPhone e novos registros recebidos pela API.
- Repetidos testes de temperatura em resoluções ×1/×2/×4/×8/×16, transações
  com STOP/repeated START e leitura de buffer preenchido previamente.
- Mantido o modo normal por 12 segundos sem reinicializações entre amostras.
  No primeiro módulo a temperatura continuou zerada; a montagem foi preservada.
- Explicada a origem matemática de −132,7 °C e documentado que o BMP ainda
  não fornece uma temperatura válida. Não foi aplicada correção artificial.
- Adicionados `scripts/diagnosticar_bmp280.py`, `scripts/empacotar.py` e
  `COMO_EXECUTAR.md`. A entrega exclui ambiente virtual, credenciais, banco
  e backups privados, mantendo o frontend existente e modelos de configuração.
- Acrescentados testes de integridade da entrega e proteção de ZIP existente.

## 2026-11-10 — Diagnóstico e proteção do BMP280

- Corrigida a pinagem do programa normal para SDA GPIO18 e SCL GPIO22.
- Driver com SoftI2C, timeout, reset e espera da calibração de fábrica,
  medição forçada T×2/P×16 e validação dos dados brutos e compensados.
- Em falha, os campos do BMP ficam nulos para permitir o envio dos demais
  sensores. Valores como −132,7 °C não seguem para a API.
- Acrescentados testes de compensação numérica, dados inválidos, timeout,
  recuperação e gravação com DHT/MQ válidos e BMP ausente. Total: 12 passaram.
- Firmware atualizado na COM5 após backup dos dois arquivos anteriores.
  O primeiro módulo ainda retorna temperatura bruta zero; isso permanece
  em diagnóstico e não foi mascarado por ajuste de temperatura.
- Detalhes e fontes em [DIAGNOSTICO_BMP280.md](DIAGNOSTICO_BMP280.md).

## 2026-11-04 — Revisão e correções

Revisão completa de todos os arquivos, seguida de diagnóstico do erro `POST /api/leituras 401`. O HTML (`frontend/index.html`) e o CSS **não foram alterados**; em `app.js` só foram corrigidos textos.

### Problemas encontrados

| # | Gravidade | Problema | Evidência |
| --- | --- | --- | --- |
| 1 | Alta | `.env` com 0 bytes: o servidor ficaria sem chave (503) ou, em processo antigo, com chave desatualizada na memória (401). | Tamanho do arquivo = 0; `config.py` possuía chave. |
| 2 | Alta | `config.example.py` (modelo, feito para ser compartilhado) continha a **chave real** da API. | Comparação por script: igual à de `config.py`. |
| 3 | Alta | O backend **nunca lia o `.env`**: `python-dotenv` estava no `requirements.txt`, mas sem uso. A chave só chegava se o terminal a exportasse. Uma `$env:API_KEY` esquecida de outra sessão vencia o arquivo. | `grep dotenv` sem resultados no código. |
| 4 | — | ~~Porta 8000 ocupada~~ e ~~IP diferente~~: **não são problemas do projeto.** Foram observados no notebook de revisão (outro do que roda a estação) e foram descartados. O projeto roda em outro notebook. | — |
| 5 | Informativo | Em hotspot de celular o IP do computador muda ao reconectar; `API_URL` precisa ser conferida no notebook que roda a API. | README, seção 2. |
| 6 | Média | Acentos corrompidos em arquivos (`?` literal, bytes `3f`): `README.md`, `frontend/app.js`, `backend/main.py`, `scripts/simular.py`, `.vscode/launch.json`. No painel, valores ausentes apareciam como `?` e textos como "Sa?da digital". | `xxd` do README; leitura de `app.js`. |
| 7 | Média | `.venv` copiado de outro computador, apontando para `C:\Users\Windows\...`; não executa aqui. | `pyvenv.cfg`; erro `did not find executable`. |
| 8 | Média | `backup_esp32/main_original_esp32.py` guarda a senha do Wi-Fi em texto puro e não estava no `.gitignore`. | `grep`. |
| 9 | Baixa | `config.example.py` com intervalo 30 s, enquanto o README dizia 5 s e o painel alerta após 30 s. Com 30 s o alerta "Sem leituras recentes" piscaria. | Leitura dos arquivos. |
| 10 | Baixa | Firmware: erro HTTP aparecia só como bytes crus; falha inesperada de um driver derrubava o laço inteiro. | Leitura de `api_client.py` e `main.py`. |
| 11 | Informativo | Projeto dentro do OneDrive com SQLite em `data/`: risco de corrupção/travamento na sincronização. | Caminho da pasta. |

### Alterações feitas

| Arquivo | Mudança | Motivo |
| --- | --- | --- |
| `.env` | Restaurado com `API_KEY` igual à de `firmware/config.py` (copiada por script, sem exibir). Estava vazio, nada foi sobrescrito. | #1 |
| `firmware/config.example.py` | Chave real trocada por `troque-por-uma-chave`; intervalo 30 → 5. | #2, #9 |
| `backend/main.py` | `load_dotenv(.env, override=True)`; função `impressao_digital()`; log de startup (chave carregada ou ausente); log de `Chave rejeitada: recebida=… esperada=…`; textos com acento. | #3, #6 e diagnóstico de 401 |
| `firmware/config.py` | **Sem alteração final.** O IP chegou a ser trocado para o do notebook de revisão e foi revertido para 172.20.10.4, o último valor conhecido do notebook que roda a estação. Confirmar com `ipconfig` lá. | #5 |
| `firmware/api_client.py` | Mensagem de erro com código HTTP e causa provável (`DICAS`). | #10 |
| `firmware/main.py` | `try/except` por sensor no laço. | #10 |
| `frontend/app.js` | Somente strings: `?` → `—`, `Saída digital · LDR`, `Sensor não detectado`, `Última leitura`, `API indisponível — …`. Lógica intacta. | #6 |
| `scripts/simular.py` | Acentos. | #6 |
| `.vscode/launch.json` | Nome da configuração com acentos. | #6 |
| `.gitignore` | `backup_esp32/`. | #8 |
| `tests/test_api.py` | +3 testes: chave errada (401, sem gravação), impressão digital não expõe a chave, payload parcial (422). | cobertura das mudanças |
| `README.md` | Reescrito com acentos corretos; novas seções (OneDrive, `.venv` não portável, `.env` com prioridade, IP de hotspot, diagnóstico por sintoma). | #6, #7, #11 |
| `CHANGELOG.md` | Este arquivo. | — |

### Decisões e alternativas

**Fonte da chave: `.env` com `override=True`.** Alternativas: (a) manter apenas variáveis de ambiente — simples, mas já causou o 401 por valor esquecido e não documentado; (b) `override=False` — respeita o terminal, porém mantém a ambiguidade. Escolhido (override): uma fonte de verdade, ao custo de `$env:API_KEY` deixar de funcionar como atalho. Deixaria de valer se o servidor for implantado em contêiner/serviço, onde variáveis de ambiente são o padrão; aí troque para `override=False` ou remova a leitura do arquivo.

**Impressão digital da chave nos logs.** SHA-256 truncado a 6 hex: permite comparar servidor × firmware sem expor o segredo. Não é um mecanismo de segurança; em rede pública não registre isso.

### Verificações executadas

- `pytest`: **5 passed** (venv temporário, Python 3.12, dependências do `requirements.txt`).
- API em porta 8001 com banco temporário e uma `API_KEY` antiga forçada no ambiente: `GET /api/saude` 200; `POST` com a chave do `config.py` → **201**; `POST` com chave errada → **401**, log com impressões digitais diferentes; `GET /` 200. O `.env` prevaleceu sobre a variável antiga.
- Banco real `data/estacao.db` **não foi modificado**: 27 leituras de `esp32-01`, última em 2026-11-04T22:20:10Z.

### Checklist de migração para o notebook que roda a estação

Esta revisão foi feita em **outro notebook**, sem ESP32 e sem rodar a estação real. Tudo que depende de hardware, rede e processos fica para a máquina de destino.

1. Copie o projeto **sem a pasta `.venv`** (ela guarda caminhos absolutos e o `.venv` desta cópia veio de outra máquina). Se o projeto voltar para o mesmo caminho original, o antigo ainda pode funcionar; na dúvida, recrie (README, seção 1).
2. Confirme que o `.env` tem `API_KEY` (não vazio) e que coincide com `firmware/config.py`. Use o comando de impressão digital do README, seção 7.
3. Rode `ipconfig` e ajuste `API_URL` em `firmware/config.py` se o IP não for mais 172.20.10.4.
4. Verifique se algo já usa a porta 8000 (`netstat -ano | Select-String ':8000'`) antes de iniciar a API.
5. Inicie a API e confira no log `API_KEY carregada (impressao digital …)`.
6. Descubra a porta COM (`mpremote connect list`) e copie `firmware/sensors`, `wifi.py`, `api_client.py`, `config.py` e `main.py` para a placa; dê `reset` (README, seção 2).
7. Observe o console da placa e o log da API: esperado `POST … 201 Created` e `Leitura salva na API`. Em 401/503/422/timeout, use a tabela do README, seção 7.
8. Confirme uma nova linha em `data/estacao.db` e rode `pytest -q` (esperado: 5 passed).
9. Se a pasta estiver no OneDrive, aponte `DATABASE_PATH` para fora dele ou pause a sincronização.

### Não verificado / pendente
- Considerar a chave atual **comprometida** (esteve em `config.example.py`): gerar outra, atualizar `.env` e `config.py`, reenviar à placa. A senha do Wi-Fi em `backup_esp32/` também deve ser trocada se o projeto tiver sido compartilhado.
- O 401 originalmente relatado (outro computador, `C:\Users\Windows\Desktop\projeto - cc`) não pôde ser reproduzido aqui: aquele caminho não existe nesta máquina. A causa mais coerente com as evidências é o processo antigo ou uma variável `API_KEY` divergente; o item #3 elimina essa classe de erro e o log de impressões digitais permite confirmar a causa da próxima vez.
- BMP280: continua sem ser detectado fisicamente; verificar fiação (README, seção 7).
