$ErrorActionPreference = "Stop"

$projectDir = $PSScriptRoot
$envFile = Join-Path $projectDir ".env"
if (-not (Test-Path -LiteralPath $envFile -PathType Leaf)) {
    throw "Missing .env file in $projectDir"
}

$pythonCommand = Get-Command py -ErrorAction SilentlyContinue
if (-not $pythonCommand) {
    throw "Python launcher 'py' was not found. Install Python 3 and try again."
}

$python = (& $pythonCommand.Source -3 -c "import sys; print(sys.executable)").Trim()
if ($LASTEXITCODE -ne 0 -or -not $python -or -not (Test-Path -LiteralPath $python)) {
    throw "Could not find the Python 3 interpreter. Install Python 3 and try again."
}

& $python -c "import telegram, dotenv, requests, bs4"
if ($LASTEXITCODE -ne 0) {
    throw "Bot dependencies are missing. Run: py -3 -m pip install -r requirements.txt"
}

$taskName = "JobScannerBot"
$action = New-ScheduledTaskAction -Execute $python -Argument "bot.py" -WorkingDirectory $projectDir
$trigger = New-ScheduledTaskTrigger -AtLogOn -User ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name)
$principal = New-ScheduledTaskPrincipal -UserId ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) -ExecutionTimeLimit ([TimeSpan]::Zero) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Description "Runs the Telegram job scanner bot at sign-in." -Force | Out-Null
Start-ScheduledTask -TaskName $taskName

Write-Host "Startup task '$taskName' installed and started."
Write-Host "The PC must stay on, awake, and connected to the internet for the bot to run."
