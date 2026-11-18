[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$raizEstacao = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$pythonJanela = Join-Path $raizEstacao '.venv\Scripts\pythonw.exe'
$iniciadorEstacao = Join-Path $raizEstacao 'scripts\iniciar_estacao.py'
$iconeEstacao = Join-Path $raizEstacao 'assets\estacao-meteorologica.ico'

foreach ($arquivoEstacao in @($pythonJanela, $iniciadorEstacao, $iconeEstacao)) {
    if (-not (Test-Path -LiteralPath $arquivoEstacao -PathType Leaf)) {
        throw ('Arquivo necessario nao encontrado: ' + $arquivoEstacao + '. Consulte COMO_EXECUTAR.md e prepare o ambiente antes de criar o atalho.')
    }
}

# O nome com hash faz o Explorer reconhecer um desenho atualizado sem apagar
# o cache do Windows nem reiniciar a area de trabalho.
$hashIconeEstacao = (Get-FileHash -LiteralPath $iconeEstacao -Algorithm SHA256).Hash
$versaoIconeEstacao = $hashIconeEstacao.Substring(0, 12).ToLowerInvariant()
$iconeAtalhoEstacao = Join-Path (Split-Path -Parent $iconeEstacao) ('estacao-meteorologica-' + $versaoIconeEstacao + '.ico')
if (-not (Test-Path -LiteralPath $iconeAtalhoEstacao -PathType Leaf) -or
    (Get-FileHash -LiteralPath $iconeAtalhoEstacao -Algorithm SHA256).Hash -ne $hashIconeEstacao) {
    Copy-Item -LiteralPath $iconeEstacao -Destination $iconeAtalhoEstacao -ErrorAction Stop
}

$desktopEstacao = [Environment]::GetFolderPath('Desktop')
if (-not (Test-Path -LiteralPath $desktopEstacao -PathType Container)) {
    throw 'A pasta da area de trabalho nao foi localizada.'
}
$nomeEstacao = [System.Text.RegularExpressions.Regex]::Unescape('Esta\u00e7\u00e3o Meteorol\u00f3gica')
$caminhoAtalho = Join-Path $desktopEstacao ($nomeEstacao + '.lnk')
$argumentosEstacao = '"' + $iniciadorEstacao + '"'
$shellEstacao = New-Object -ComObject WScript.Shell

try {
    if (Test-Path -LiteralPath $caminhoAtalho -PathType Leaf) {
        $atalhoAnterior = $shellEstacao.CreateShortcut($caminhoAtalho)
        if ($atalhoAnterior.TargetPath -ne $pythonJanela -or $atalhoAnterior.Arguments -ne $argumentosEstacao) {
            $pastaBackupAtalho = Join-Path $raizEstacao '.tools\atalhos_anteriores'
            New-Item -ItemType Directory -Path $pastaBackupAtalho -Force | Out-Null
            $backupAtalho = Join-Path $pastaBackupAtalho ('atalho-' + (Get-Date -Format 'yyyyMMdd-HHmmss-fff') + '.lnk')
            Copy-Item -LiteralPath $caminhoAtalho -Destination $backupAtalho -ErrorAction Stop
            Write-Host ('Atalho anterior preservado em: ' + $backupAtalho)
        }
        [System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($atalhoAnterior) | Out-Null
    }

    $atalhoEstacao = $shellEstacao.CreateShortcut($caminhoAtalho)
    $atalhoEstacao.TargetPath = $pythonJanela
    $atalhoEstacao.Arguments = $argumentosEstacao
    $atalhoEstacao.WorkingDirectory = $raizEstacao
    $atalhoEstacao.IconLocation = $iconeAtalhoEstacao + ',0'
    $atalhoEstacao.Description = 'Iniciar a estacao meteorologica e abrir o painel no navegador.'
    $atalhoEstacao.WindowStyle = 1
    $atalhoEstacao.Save()
    [System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($atalhoEstacao) | Out-Null

    if (-not (Test-Path -LiteralPath $caminhoAtalho -PathType Leaf)) {
        throw 'O Windows nao confirmou a criacao do atalho.'
    }
    Write-Host ('Atalho criado: ' + $caminhoAtalho)
    Write-Host 'Clique duas vezes no icone para abrir a estacao.'
}
finally {
    [System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($shellEstacao) | Out-Null
}
