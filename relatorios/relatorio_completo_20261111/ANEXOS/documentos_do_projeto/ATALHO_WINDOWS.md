# Estação Meteorológica — abrir pelo ícone do Windows

O atalho **Estação Meteorológica** abre o painel no navegador padrão. Quando o
servidor ainda não está ligado, ele também inicia o FastAPI em um terminal e
espera a API ficar pronta. Quando a estação já está atendendo na porta 8000,
ele abre o painel usando essa instância.

## Usar no notebook atual

1. Conecte o notebook à rede usada pelo ESP32.
2. Ligue a estação na fonte/tomada ou na USB.
3. Dê dois cliques em **Estação Meteorológica**, na área de trabalho.
4. Aguarde o navegador e confira o horário da última leitura.

O ESP32 pode funcionar alimentado pela fonte, sem cabo USB no notebook, pois
envia os dados por Wi-Fi. O computador precisa permanecer ligado, com o
servidor ativo e acessível na rede. A tomada alimenta o ESP32; ela não inicia
o servidor do computador.

O painel abre mesmo sem novas amostras do ESP32. Nesse caso ele pode mostrar
os registros já salvos e o aviso de que não há leituras recentes. Para novos
dados, placa e notebook devem conseguir se comunicar na rede, a chave precisa
coincidir e a `API_URL` da placa precisa apontar para o IP atual do notebook.
O endereço `localhost` é usado pelo navegador no notebook, não pela placa.

O hotspot pode entregar outro IP quando o computador reconecta. Se isso
acontecer, confira `ipconfig` e atualize a configuração da placa seguindo
[COMO_EXECUTAR.md](COMO_EXECUTAR.md). O atalho não altera a rede, o firmware ou
as configurações dos sensores.

## Terminal e encerramento

Quando inicia uma nova instância, o terminal mostra as mensagens do servidor.
Mantenha-o aberto durante a coleta. Para encerrar, pressione **Ctrl+C** nesse
terminal ou feche sua janela. Fechar somente a aba do navegador mantém o
servidor recebendo dados.

Se já havia servidor rodando, outro clique apenas abre o painel; não inicia
um segundo servidor. Se a porta 8000 estiver ocupada por outro serviço, o
iniciador informa o problema. Ele não encerra esse programa nem escolhe outra
porta automaticamente, porque o ESP32 envia para a porta configurada.

O atalho só inicia quando você clica. Ele não instala um serviço do Windows
nem configura inicialização automática ao ligar o notebook.

## Criar o atalho em outro computador ou depois de mover o projeto

Primeiro extraia o ZIP e prepare a `.venv`, dependências, `.env` e configuração
da placa conforme [COMO_EXECUTAR.md](COMO_EXECUTAR.md). Não copie a `.venv` do
notebook original. Depois, no PowerShell da pasta do projeto:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\criar_atalho.ps1
```

O comando cria o atalho na área de trabalho do usuário atual. A opção de
execução aplica-se somente a esse processo; não muda a política permanente do
Windows. Se um atalho com o mesmo nome apontar para outro local, o instalador
guarda uma cópia em `.tools/atalhos_anteriores/` antes de atualizá-lo.

Recrie o atalho depois de mover a pasta, trocar de computador ou extrair uma
nova cópia do projeto. O arquivo `.lnk` da área de trabalho referencia a pasta
local; no ZIP seguem o instalador e os ícones para cada integrante criar o seu.

## Arquivos do recurso

| Arquivo | Função |
| --- | --- |
| `scripts/iniciar_estacao.py` | Confere o servidor, inicia o FastAPI quando necessário e abre o navegador; trata cliques simultâneos e mensagens de erro. |
| `scripts/criar_atalho.ps1` | Cria o atalho com nome, ícone e caminhos da instalação atual. |
| `assets/estacao-meteorologica.svg` | Rosa dos ventos vetorial editável de oito pontas, em branco e verde `#183b38`, sem letras e com fundo transparente. |
| `assets/estacao-meteorologica.ico` | Ícone do Windows em 16, 24, 32, 48, 64, 128 e 256 pixels, com transparência. |
| `assets/estacao-meteorologica.png` | Prévia de 512×512 pixels da rosa dos ventos de oito pontas, em branco e verde `#183b38`, sem letras e com fundo transparente, renderizada a partir do SVG. |
| `frontend/favicon.svg` | O mesmo vetor na aba do navegador, para combinar com o atalho. |

O instalador também gera uma cópia do ICO com identificação da versão no nome,
para o Windows exibir o desenho atualizado sem precisar reiniciar o Explorer.

O ícone é um recurso local e não exige serviço externo, conta ou conexão com
a internet. Para usar o atalho, não é necessário instalar bibliotecas de
desenho nem abrir o VS Code.

## Se não abrir

| Sintoma | Próximo passo |
| --- | --- |
| Atalho não encontra Python/pasta | Recriar `.venv` se necessário e executar novamente `criar_atalho.ps1`. |
| Falta configuração ou dependência | Seguir a preparação de `COMO_EXECUTAR.md`, sem substituir configurações já preenchidas. |
| Porta 8000 ocupada por outra aplicação | Identificar o programa no notebook; o atalho preserva esse processo. |
| Erro ao iniciar o servidor | Ler a mensagem do terminal e a orientação exibida pelo iniciador. |
| Navegador não abre automaticamente | Abrir `http://localhost:8000/` após confirmar que o servidor iniciou. |
| Painel abre com dados antigos | Conferir alimentação da placa, rede, IP de destino e horário da última recepção. |
| Só o BMP280 fica sem medida | Usar o [relatório de recuperação](RELATORIO_FUNCIONAMENTO_E_RECUPERACAO_BMP280.md); abrir o painel não recalibra o sensor. |

## Verificação desta versão

O atalho real foi executado e abriu o navegador, mantendo o mesmo processo
que já atendia na porta 8000. Em um ambiente temporário separado, o modo
servidor iniciou, serviu o painel e persistiu uma amostra de teste em outro
banco e porta. O processo temporário foi encerrado ao final; a estação
original permaneceu ativa. O conjunto completo teve **46 testes passando**.

Referências das interfaces utilizadas: [atalhos WSH da Microsoft](https://learn.microsoft.com/en-us/troubleshoot/windows-client/admin-development/create-desktop-shortcut-with-wsh),
[abertura de navegador pelo Python](https://docs.python.org/3/library/webbrowser.html)
e [processos e console do Windows](https://docs.python.org/3/library/subprocess.html).
