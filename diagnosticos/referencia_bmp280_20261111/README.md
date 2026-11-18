# Evidências de referência do BMP280 — 11/11/2026

Relatório principal: [RELATORIO_FUNCIONAMENTO_E_RECUPERACAO_BMP280.md](../../RELATORIO_FUNCIONAMENTO_E_RECUPERACAO_BMP280.md).

Esta pasta preserva as evidências do funcionamento recuperado e duas janelas de comparação com temperatura bruta zero. A exportação foi feita às 14:40:09, horário de Brasília (UTC−3), em uma transação SQLite somente leitura.

## Conteúdo

- `continuidade_banco.json`: 217 registros da estação `esp32-01`, IDs 3443–3659, resumo e amostras históricas. Todos os 217 têm temperatura BMP e pressão preenchidas. O banco não identifica individualmente qual BMP estava conectado.
- `leituras_desde_recuperacao.csv`: os mesmos registros para planilha. Os números do arquivo usam ponto decimal; o painel formata com vírgula. A coluna `gas` é ADC bruto.
- `amostras_*.jsonl`: uma amostra do monitor por linha; cada janela contém 18 tentativas. `142031` é a janela válida; `141604` corresponde ao HW-611 confirmado pelo usuário; `133700` é uma janela anterior de falha.
- `resumos_monitores.json`: início/fim, contexto da identificação física, calibração e SHA-256 dos logs originais.
- `contexto_*.json`: metadados preservados dos testes e observações da API após reset. A identificação contextual do segundo módulo não é uma certificação eletrônica individual.
- `fontes/`: cópias de referência dos arquivos públicos do computador. Não instalar automaticamente na placa; configurações privadas foram excluídas.
- `painel_142705.png`: captura do navegador com leituras reais e histórico.
- `manifesto_sha256.json`: integridade dos demais arquivos desta pasta. Ele não inclui o próprio hash nem certifica autenticidade do sensor.

## Conferir integridade

Na raiz do projeto:

```powershell
$baseReferencia = Join-Path $PWD 'diagnosticos\referencia_bmp280_20261111'
$manifestoReferencia = Get-Content -LiteralPath (Join-Path $baseReferencia 'manifesto_sha256.json') -Raw -Encoding UTF8 | ConvertFrom-Json
foreach ($itemReferencia in $manifestoReferencia.arquivos) {
    $caminhoReferencia = Join-Path $baseReferencia $itemReferencia.caminho
    $hashReferencia = (Get-FileHash -LiteralPath $caminhoReferencia -Algorithm SHA256).Hash
    if ($hashReferencia -ne $itemReferencia.sha256) {
        throw ('Arquivo diferente da referencia: ' + $itemReferencia.caminho)
    }
}
Write-Host 'Hashes conferidos.'
```

## Uso

Guardar esta pasta junto do relatório. Abrir o relatório pela raiz do projeto mantém os links funcionando. As evidências não contêm `.env`, `config.py`, senha Wi-Fi, chave de API ou imagem de flash. CSV e JSON são exportações de consulta e não devem substituir o banco ativo.

Não editar as evidências ao registrar uma falha nova: criar outra pasta com nova data/hora e outra ficha de ocorrência. O hash permite detectar mudanças nos arquivos, mas não identifica fisicamente o módulo.
