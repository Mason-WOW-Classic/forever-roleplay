$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$pythonCandidates = @(
    (Join-Path $env:LOCALAPPDATA 'Programs/Python/Python313/pythonw.exe'),
    (Join-Path $env:LOCALAPPDATA 'Programs/Python/Python312/pythonw.exe'),
    (Join-Path $env:USERPROFILE '.cache/codex-runtimes/codex-primary-runtime/dependencies/python/pythonw.exe')
)
$pythonPath = $pythonCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if (-not $pythonPath) {
    $pythonCommand = Get-Command pythonw.exe -ErrorAction SilentlyContinue
    if ($pythonCommand) { $pythonPath = $pythonCommand.Source }
}
if (-not $pythonPath) {
    throw 'Python 3.10+ with Tkinter is required. Install Python from python.org or run: python -m companion.app'
}
Start-Process -FilePath $pythonPath -ArgumentList @('-m', 'companion.app') -WorkingDirectory $projectRoot -WindowStyle Hidden
