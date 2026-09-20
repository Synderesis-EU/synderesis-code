# Synderesis Code native Windows installer. No administrator access required.
& {
    $ErrorActionPreference = 'Stop'
    if ($env:OS -ne 'Windows_NT') { throw 'Use the shell installer on macOS or Linux.' }
    $Version = '0.1.0-alpha.1'
    if ([System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture -ne 'X64') {
        throw 'This release requires 64-bit x86 Windows. See https://github.com/Synderesis-EU/synderesis-code/releases'
    }
    $Asset = "synderesis-code-$Version-windows-x86_64.zip"
    $Base = "https://github.com/Synderesis-EU/synderesis-code/releases/download/v$Version"
    Write-Host "Installing Synderesis Code $Version..."
    $Temp = Join-Path ([IO.Path]::GetTempPath()) ([Guid]::NewGuid().ToString())
    New-Item -ItemType Directory -Path $Temp | Out-Null
    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest "$Base/$Asset" -OutFile "$Temp/$Asset" -UseBasicParsing
        Invoke-WebRequest "$Base/SHA256SUMS" -OutFile "$Temp/SHA256SUMS" -UseBasicParsing
        $Checksums = Get-Content -LiteralPath "$Temp/SHA256SUMS" -Raw
        $Pattern = '(?m)^([a-f0-9]{64})\s+' + [regex]::Escape($Asset) + '\s*$'
        $Match = [regex]::Match($Checksums, $Pattern)
        if (-not $Match.Success) { throw 'Missing or invalid release checksum.' }
        $Actual = (Get-FileHash "$Temp/$Asset" -Algorithm SHA256).Hash.ToLower()
        if ($Actual -ne $Match.Groups[1].Value) { throw 'Release checksum mismatch.' }
        Expand-Archive "$Temp/$Asset" "$Temp/unpacked"
        $InstallDir = if ($env:SYNDERESIS_INSTALL_DIR) { $env:SYNDERESIS_INSTALL_DIR } else { Join-Path $env:LOCALAPPDATA 'SynderesisCode/bin' }
        New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
        & "$Temp/unpacked/synderesis-code.exe" --version
        if ($LASTEXITCODE -ne 0) { throw 'Installed executable failed its version check.' }
        Copy-Item "$Temp/unpacked/synderesis-code.exe" "$InstallDir/synderesis-code.exe.new" -Force
        Move-Item "$InstallDir/synderesis-code.exe.new" "$InstallDir/synderesis-code.exe" -Force
        $UserPath = [string][Environment]::GetEnvironmentVariable('Path', 'User')
        if (($UserPath -split ';') -notcontains $InstallDir) {
            [Environment]::SetEnvironmentVariable('Path', ($UserPath.TrimEnd(';') + ';' + $InstallDir).TrimStart(';'), 'User')
        }
        if (($env:Path -split ';') -notcontains $InstallDir) { $env:Path += ";$InstallDir" }
        Write-Host "Installed to $InstallDir/synderesis-code.exe"
        Write-Host 'Sign in: synderesis-code login'
        Write-Host 'Start:   synderesis-code'
    } finally {
        Remove-Item $Temp -Recurse -Force
    }
}
