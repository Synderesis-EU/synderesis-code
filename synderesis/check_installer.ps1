$ErrorActionPreference = 'Stop'
$global:SynderesisFixtureArchive = (Resolve-Path fixture/synderesis-code-windows-x86_64.zip).Path
$global:SynderesisFixtureDigest = (Get-FileHash $global:SynderesisFixtureArchive -Algorithm SHA256).Hash.ToLower()
function Invoke-WebRequest {
  param([string]$Uri, [string]$OutFile, [switch]$UseBasicParsing)
  if ($Uri -notlike 'https://github.com/Synderesis-EU/synderesis-code/releases/download/*') { throw 'Unexpected download origin' }
  $Url = [Uri]$Uri
  if ($Url.AbsolutePath.EndsWith('/SHA256SUMS')) {
    if ($Url.Query -notmatch '^\?check=[a-f0-9-]{36}$') { throw 'Checksum request must bypass stale cache' }
    "$global:SynderesisFixtureDigest  synderesis-code-0.1.0-alpha.1-windows-x86_64.zip" | Set-Content -LiteralPath $OutFile -Encoding ascii
  } else {
    if ($Url.Query -ne "?sha256=$global:SynderesisFixtureDigest") { throw 'Archive request must be bound to its digest' }
    Copy-Item $global:SynderesisFixtureArchive $OutFile
  }
}
$env:SYNDERESIS_INSTALL_DIR = "$env:RUNNER_TEMP/installer-check"
& ./synderesis/install.ps1
$exe = "$env:SYNDERESIS_INSTALL_DIR/synderesis-code.exe"
& $exe --help
if ($LASTEXITCODE -ne 0) { throw 'Installed executable help failed' }
$before = (Get-FileHash $exe -Algorithm SHA256).Hash
$global:SynderesisFixtureDigest = '0' * 64
$rejected = $false
try { & ./synderesis/install.ps1 }
catch { if ($_ -notmatch 'checksum mismatch') { throw }; $rejected = $true }
if (-not $rejected) { throw 'Corrupted archive was accepted' }
if ((Get-FileHash $exe -Algorithm SHA256).Hash -ne $before) { throw 'Failed install changed executable' }
Write-Host 'PASS: native install, executable startup, and corruption rejection'
