@echo off
setlocal DisableDelayedExpansion
rem Synderesis Code installer for Windows Command Prompt. No administrator access required.
set "SYNDERESIS_CMD_POWERSHELL=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
if exist "%SystemRoot%\Sysnative\WindowsPowerShell\v1.0\powershell.exe" set "SYNDERESIS_CMD_POWERSHELL=%SystemRoot%\Sysnative\WindowsPowerShell\v1.0\powershell.exe"
if not exist "%SYNDERESIS_CMD_POWERSHELL%" (
    echo Windows PowerShell is required to install Synderesis Code. 1>&2
    exit /b 1
)
set "SYNDERESIS_CMD_INSTALL_DIR=%SYNDERESIS_INSTALL_DIR%"
if not defined SYNDERESIS_CMD_INSTALL_DIR set "SYNDERESIS_CMD_INSTALL_DIR=%LOCALAPPDATA%\SynderesisCode\bin"
set "SYNDERESIS_INSTALL_DIR=%SYNDERESIS_CMD_INSTALL_DIR%"
"%SYNDERESIS_CMD_POWERSHELL%" -NoLogo -NoProfile -NonInteractive -Command "$ErrorActionPreference = 'Stop'; $ProgressPreference = 'SilentlyContinue'; try { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-RestMethod 'https://www.synderesis.eu/cli/install.ps1' | Invoke-Expression } catch { [Console]::Error.WriteLine($_.Exception.Message); exit 1 }"
if errorlevel 1 exit /b 1
rem Keep the installed command available in the calling Command Prompt.
endlocal & set "PATH=%SYNDERESIS_CMD_INSTALL_DIR%;%PATH%"
exit /b 0
