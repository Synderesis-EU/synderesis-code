# Exercise the real installer gate without downloading or changing an installation.
$ErrorActionPreference = 'Stop'
$SavedOS = $env:OS
$SavedArchitecture = $env:PROCESSOR_ARCHITECTURE
$SavedNativeArchitecture = $env:PROCESSOR_ARCHITEW6432
function Invoke-WebRequest {
    param([string]$Uri, [string]$OutFile, [switch]$UseBasicParsing)
    throw 'Architecture accepted: download intercepted'
}
try {
    $env:OS = 'Windows_NT'
    $Cases = @(
        @{ Process = 'AMD64'; Native = ''; Accepted = $true },
        @{ Process = 'x86'; Native = 'AMD64'; Accepted = $true },
        @{ Process = 'X64'; Native = ''; Accepted = $true },
        @{ Process = 'ARM64'; Native = ''; Accepted = $false },
        @{ Process = 'AMD64'; Native = 'ARM64'; Accepted = $false },
        @{ Process = 'x86'; Native = ''; Accepted = $false },
        @{ Process = 'unknown'; Native = ''; Accepted = $false }
    )
    foreach ($Case in $Cases) {
        $env:PROCESSOR_ARCHITECTURE = $Case.Process
        $env:PROCESSOR_ARCHITEW6432 = $Case.Native
        $Failure = ''
        try { & "$PSScriptRoot/install.ps1" }
        catch { $Failure = $_.Exception.Message }
        if ($Case.Accepted) {
            if ($Failure -ne 'Architecture accepted: download intercepted') {
                throw "Expected acceptance for $($Case.Process)/$($Case.Native), got: $Failure"
            }
        } elseif ($Failure -notlike 'Detected Windows architecture*') {
            throw "Expected rejection for $($Case.Process)/$($Case.Native), got: $Failure"
        }
    }
    Write-Host "PASS: $($Cases.Count) installer architecture cases"
} finally {
    $env:OS = $SavedOS
    $env:PROCESSOR_ARCHITECTURE = $SavedArchitecture
    $env:PROCESSOR_ARCHITEW6432 = $SavedNativeArchitecture
}
