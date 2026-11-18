<#
.SYNOPSIS
Restaura a flash integral do ESP32 a partir de um backup privado verificado.

.DESCRIPTION
Valida manifesto, duas imagens de 4 MiB e identidade MAC antes de escrever.
Depois da escrita, executa verify-flash sem --diff. A placa so recebe o comando
final de reinicio se escrita e verificacao terminarem com codigo zero.
Nao apaga banco/projeto, nao executa erase-flash e nao altera eFuses.

.EXAMPLE
.\scripts\restaurar_flash_esp32.ps1 -BackupDirectory backup_esp32\antes_arduino_20261111_123005 -Port COM5

O script e um utilitario manual: le-lo ou validar sua sintaxe nao o executa.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$BackupDirectory,

    [ValidatePattern('^COM[1-9][0-9]*$')]
    [string]$Port = 'COM5'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Assert-PlainItem {
    param([Parameter(Mandatory = $true)]$Item)
    if (($Item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
        throw ('Links e junctions nao sao aceitos neste caminho: ' + $Item.FullName)
    }
}

function Get-BackupImage {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][string]$Directory,
        [Parameter(Mandatory = $true)][long]$ExpectedBytes,
        [Parameter(Mandatory = $true)][string]$ExpectedHash
    )
    # O manifesto deve conter apenas um nome de arquivo local, nunca comandos,
    # diretorios, caminhos absolutos ou streams alternativos do Windows.
    if ($Name -notmatch '^[A-Za-z0-9][A-Za-z0-9_.-]*\.bin$' -or
        [IO.Path]::GetFileName($Name) -cne $Name) {
        throw 'Nome de imagem invalido no manifesto'
    }
    $image = Get-Item -LiteralPath (Join-Path $Directory $Name) -Force
    Assert-PlainItem -Item $image
    if ($image.PSIsContainer -or $image.Length -ne $ExpectedBytes) {
        throw ('Imagem ausente ou com tamanho diferente do manifesto: ' + $Name)
    }
    if (-not [string]::Equals($image.Directory.FullName, $Directory,
                             [StringComparison]::OrdinalIgnoreCase)) {
        throw 'A imagem deve estar diretamente dentro da pasta de backup'
    }
    $hash = (Get-FileHash -LiteralPath $image.FullName -Algorithm SHA256).Hash
    if (-not [string]::Equals($hash, $ExpectedHash, [StringComparison]::OrdinalIgnoreCase)) {
        throw ('SHA-256 diferente do manifesto; restauracao cancelada: ' + $Name)
    }
    return $image
}

function Invoke-EsptoolChecked {
    param(
        [Parameter(Mandatory = $true)][string[]]$Arguments,
        [switch]$CaptureOutput
    )
    # Arrays sao passados diretamente ao executavel: nada e interpretado como
    # um novo comando de shell. A saida nao inclui bytes da flash nem segredos.
    $previousPreference = $ErrorActionPreference
    $exitCode = $null
    $lines = @()
    try {
        # Windows PowerShell 5 pode transformar stderr nativo em ErrorRecord
        # mesmo com exit 0. A captura usa Continue; a decisao usa o exit code.
        $ErrorActionPreference = 'Continue'
        $lines = @(& $script:PythonExecutable @Arguments 2>&1)
        $exitCode = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $previousPreference
    }
    if ($null -eq $exitCode) {
        throw 'esptool nao forneceu codigo de saida; sequencia interrompida'
    }
    $outputText = ($lines | ForEach-Object { $_.ToString() }) -join [Environment]::NewLine
    if (-not $CaptureOutput -or $exitCode -ne 0) {
        foreach ($line in $lines) {
            Write-Host $line.ToString()
        }
    }
    if ($exitCode -ne 0) {
        throw ('esptool terminou com codigo ' + $exitCode + '; sequencia interrompida')
    }
    return [PSCustomObject]@{ ExitCode = $exitCode; Output = $outputText }
}

$projectRoot = (Get-Item -LiteralPath (Split-Path -Parent $PSScriptRoot) -Force).FullName
$backupBase = Get-Item -LiteralPath (Join-Path $projectRoot 'backup_esp32') -Force
Assert-PlainItem -Item $backupBase
if (-not $backupBase.PSIsContainer) {
    throw 'backup_esp32 nao e um diretorio'
}

$requestedDirectory = $BackupDirectory
if (-not [IO.Path]::IsPathRooted($requestedDirectory)) {
    $requestedDirectory = Join-Path $projectRoot $requestedDirectory
}
$backup = Get-Item -LiteralPath ([IO.Path]::GetFullPath($requestedDirectory)) -Force
Assert-PlainItem -Item $backup
if (-not $backup.PSIsContainer -or
    -not [string]::Equals($backup.Parent.FullName, $backupBase.FullName,
                         [StringComparison]::OrdinalIgnoreCase)) {
    throw 'BackupDirectory deve ser uma pasta filha direta de backup_esp32 do projeto'
}

$manifestFile = Get-Item -LiteralPath (Join-Path $backup.FullName 'flash_manifest.json') -Force
Assert-PlainItem -Item $manifestFile
if ($manifestFile.PSIsContainer) {
    throw 'flash_manifest.json precisa ser um arquivo'
}
$manifest = Get-Content -LiteralPath $manifestFile.FullName -Raw -Encoding UTF8 | ConvertFrom-Json
if ([int]$manifest.versao -ne 1) {
    throw 'Versao do manifesto nao suportada'
}
if ($manifest.duas_leituras_identicas -isnot [bool] -or
    -not $manifest.duas_leituras_identicas) {
    throw 'O manifesto nao confirma duas leituras de flash identicas'
}
# Este utilitario destina-se ao ESP32 classico da estacao, nao ESP32-S2/S3/C3.
if ($manifest.chip -isnot [string] -or
    $manifest.chip -notmatch '^ESP32(?:-D0WD(?:Q[56]|-V3)?)?$') {
    throw 'O manifesto nao identifica um ESP32 classico compativel com este utilitario'
}
if ([long]$manifest.flash_bytes -ne 4194304) {
    throw 'Este utilitario exige uma imagem integral de flash de 4194304 bytes'
}
if ($manifest.secure_boot -isnot [bool] -or $manifest.secure_boot -or
    $manifest.flash_encryption -isnot [bool] -or $manifest.flash_encryption) {
    throw 'Este utilitario exige secure_boot=false e flash_encryption=false confirmados'
}
if ($manifest.sha256 -isnot [string] -or $manifest.sha256 -notmatch '^[0-9A-Fa-f]{64}$') {
    throw 'SHA-256 invalido no manifesto'
}
if ($manifest.mac -isnot [string] -or
    $manifest.mac -notmatch '^(?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$') {
    throw 'MAC esperado ausente ou invalido no manifesto'
}

$imageA = Get-BackupImage -Name $manifest.imagem_restauracao -Directory $backup.FullName `
    -ExpectedBytes 4194304 -ExpectedHash $manifest.sha256
$imageB = Get-BackupImage -Name $manifest.imagem_conferencia -Directory $backup.FullName `
    -ExpectedBytes 4194304 -ExpectedHash $manifest.sha256
if ([string]::Equals($imageA.FullName, $imageB.FullName, [StringComparison]::OrdinalIgnoreCase)) {
    throw 'As duas leituras precisam estar em arquivos distintos'
}

$python = Get-Item -LiteralPath (Join-Path $projectRoot '.venv\Scripts\python.exe') -Force
if ($python.PSIsContainer) {
    throw 'Python do ambiente virtual nao encontrado'
}
$script:PythonExecutable = $python.FullName
$common = @('-m', 'esptool', '--chip', 'esp32', '--port', $Port, '--baud', '115200')

Write-Host 'Manifesto e duas imagens validados. Consultando a identidade da placa...'
# A consulta termina em hard-reset. Se a identidade divergir, o programa
# temporario volta ao boot normal, mas nenhuma imagem e escrita.
$identity = Invoke-EsptoolChecked -Arguments ($common + @(
    '--before', 'default-reset', '--after', 'hard-reset', 'read-mac'
)) -CaptureOutput
$cleanIdentity = $identity.Output -replace '\x1B\[[0-?]*[ -/]*[@-~]', ''
$matchesMac = [regex]::Matches($cleanIdentity,
    '(?im)^\s*MAC:\s*([0-9a-f]{2}(?::[0-9a-f]{2}){5})(?:\s|$)')
$observedMacs = @($matchesMac | ForEach-Object { $_.Groups[1].Value.ToLowerInvariant() } |
                 Select-Object -Unique)
if ($observedMacs.Count -ne 1 -or
    -not [string]::Equals($observedMacs[0], $manifest.mac, [StringComparison]::OrdinalIgnoreCase)) {
    throw 'MAC da placa nao coincide com o manifesto, ou nao foi identificado; nenhuma escrita iniciada'
}

Write-Host 'Identidade confirmada. Restaurando a imagem integral a 115200 baud...'
$null = Invoke-EsptoolChecked -Arguments ($common + @(
    '--before', 'default-reset', '--after', 'no-reset', 'write-flash',
    '--flash-mode', 'keep', '--flash-freq', 'keep', '--flash-size', 'keep',
    '0x0', $imageA.FullName
))

Write-Host 'Escrita concluida. Verificando toda a imagem, sem imprimir diferencas...'
$null = Invoke-EsptoolChecked -Arguments ($common + @(
    '--before', 'no-reset', '--after', 'no-reset', 'verify-flash',
    '0x0', $imageA.FullName
))

# Somente as duas operacoes acima com codigo zero permitem sair do bootloader.
Write-Host 'Imagem verificada. Retomando o boot normal...'
$null = Invoke-EsptoolChecked -Arguments ($common + @(
    '--before', 'no-reset', '--after', 'hard-reset', 'flash-id'
))
Write-Host 'Restauracao verificada e reinicio solicitado. Confira MicroPython e arquivos pela serial.'
Write-Host 'O banco SQLite, as fontes e as configuracoes do computador nao foram modificados.'
