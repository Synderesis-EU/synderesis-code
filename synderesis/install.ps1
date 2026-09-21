# Synderesis Code native Windows installer. No administrator access required.
& {
    $ErrorActionPreference = 'Stop'
    if ($env:OS -ne 'Windows_NT') { throw 'Use the shell installer on macOS or Linux.' }
    $Version = '0.1.0-alpha.1'
    # Prefer the native Windows architecture, including from a 32-bit PowerShell
    # process. RuntimeInformation can report the process architecture on older .NET.
    $Architecture = if ($env:PROCESSOR_ARCHITEW6432) {
        $env:PROCESSOR_ARCHITEW6432
    } elseif ($env:PROCESSOR_ARCHITECTURE) {
        $env:PROCESSOR_ARCHITECTURE
    } else {
        [string][System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture
    }
    $RuntimeArch = [string][System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture
    if ($Architecture -notin @('AMD64', 'X64', 'ARM64') -and $RuntimeArch -notin @('X64', 'Arm64')) {
        throw "Detected Windows architecture '$Architecture'. This release supports 64-bit Windows (Intel/AMD and ARM64 via x64 emulation). See https://github.com/Synderesis-EU/synderesis-code/releases"
    }
    $Asset = "synderesis-code-$Version-windows-x86_64.zip"
    $Base = "https://github.com/Synderesis-EU/synderesis-code/releases/download/v$Version"
    Write-Host "Installing Synderesis Code $Version..."
    $Temp = Join-Path ([IO.Path]::GetTempPath()) ([Guid]::NewGuid().ToString())
    New-Item -ItemType Directory -Path $Temp | Out-Null
    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest "$Base/SHA256SUMS?check=$([Guid]::NewGuid().ToString())" -OutFile "$Temp/SHA256SUMS" -UseBasicParsing
        $Checksums = Get-Content -LiteralPath "$Temp/SHA256SUMS" -Raw
        $Pattern = '(?m)^([a-f0-9]{64})\s+' + [regex]::Escape($Asset) + '\s*$'
        $Match = [regex]::Match($Checksums, $Pattern)
        if (-not $Match.Success) { throw 'Missing or invalid release checksum.' }
        # Bind the asset cache to its verified release digest, even within the same alpha tag.
        Invoke-WebRequest "$Base/${Asset}?sha256=$($Match.Groups[1].Value)" -OutFile "$Temp/$Asset" -UseBasicParsing
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
