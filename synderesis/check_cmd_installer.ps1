param([ValidateSet('x64','x86')][string]$Architecture = 'x64')
$ErrorActionPreference = 'Stop'
$Cmd = if ($Architecture -eq 'x86') { "$env:SystemRoot/SysWOW64/cmd.exe" } else { "$env:SystemRoot/System32/cmd.exe" }
$Launcher = (Resolve-Path "$PSScriptRoot/install.cmd").Path
$env:SYNDERESIS_INSTALL_DIR = Join-Path $env:RUNNER_TEMP "Synderesis CMD $Architecture test"
$Runner = Join-Path $env:RUNNER_TEMP "cmd-installer-$Architecture.cmd"
@"
@echo off
call "$Launcher"
if errorlevel 1 exit /b 1
where synderesis-code
if errorlevel 1 exit /b 1
synderesis-code --version
if errorlevel 1 exit /b 1
synderesis-code --help > nul
if errorlevel 1 exit /b 1
exit /b 0
"@ | Set-Content -LiteralPath $Runner -Encoding ascii
& $Cmd /d /c $Runner
if ($LASTEXITCODE -ne 0) { throw 'CMD install or same-window PATH/startup failed' }
$Installed = Join-Path $env:SYNDERESIS_INSTALL_DIR 'synderesis-code.exe'
$Before = (Get-FileHash -LiteralPath $Installed -Algorithm SHA256).Hash
if ($env:EXPECTED_BINARY_SHA256) {
    if ($env:EXPECTED_BINARY_SHA256 -notmatch '^[a-fA-F0-9]{64}$' -or $Before -ne $env:EXPECTED_BINARY_SHA256) {
        throw 'Public installer returned a different executable than the verified release'
    }
}
# A file where the install directory should be must fail visibly and nonzero.
$env:SYNDERESIS_INSTALL_DIR = Join-Path $env:RUNNER_TEMP "cmd-blocked-$Architecture"
'preserve this file' | Set-Content -LiteralPath $env:SYNDERESIS_INSTALL_DIR -Encoding ascii
& $Cmd /d /c $Launcher
if ($LASTEXITCODE -eq 0) { throw 'CMD launcher hid installer failure' }
if ((Get-Content -LiteralPath $env:SYNDERESIS_INSTALL_DIR -Raw).Trim() -ne 'preserve this file') { throw 'Failure overwrote existing file' }
if ((Get-FileHash -LiteralPath $Installed -Algorithm SHA256).Hash -ne $Before) { throw 'Failure changed existing executable' }
Write-Host "PASS: $Architecture CMD install, spaces in path, same-window command, help/version, failure propagation and preserved files"
exit 0
