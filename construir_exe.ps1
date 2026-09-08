# Construye ParkingControl.exe a partir de lanzador.py usando PyInstaller.
# Uso:  .\construir_exe.ps1
#
# El ejecutable resultante es un lanzador ligero (solo libreria estandar):
# no empaqueta Django ni las dependencias, se apoya en el Python del equipo.

$ErrorActionPreference = 'Stop'
Set-Location -Path $PSScriptRoot

# --- 1. Interprete con el que se construye -----------------------------------
$python = $null
foreach ($candidato in @('env\Scripts\python.exe', '.venv\Scripts\python.exe', 'venv\Scripts\python.exe')) {
    if (Test-Path $candidato) { $python = (Resolve-Path $candidato).Path; break }
}
if (-not $python) {
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($cmd) { $python = $cmd.Source }
}
if (-not $python) {
    Write-Host 'ERROR: no se encontro Python para construir el ejecutable.' -ForegroundColor Red
    exit 1
}
Write-Host "Python de construccion: $python" -ForegroundColor Cyan

# --- 2. PyInstaller ----------------------------------------------------------
Write-Host 'Instalando/verificando PyInstaller...' -ForegroundColor Cyan
& $python -m pip install --disable-pip-version-check pyinstaller
if ($LASTEXITCODE -ne 0) {
    Write-Host 'ERROR: fallo la instalacion de PyInstaller.' -ForegroundColor Red
    exit 1
}

# --- 3. Icono (opcional) -----------------------------------------------------
New-Item -ItemType Directory -Force -Path 'build' | Out-Null
$png = Join-Path $PSScriptRoot 'app_page\static\app_page\img\index.png'
$icono = Join-Path $PSScriptRoot 'build\ParkingControl.ico'
$usarIcono = $false
if (Test-Path $png) {
    & $python -c "from PIL import Image; Image.open(r'$png').convert('RGBA').save(r'$icono', sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)])"
    if ($LASTEXITCODE -eq 0) {
        if (Test-Path $icono) { $usarIcono = $true }
    }
}
if ($usarIcono) {
    Write-Host "Icono generado: $icono" -ForegroundColor Cyan
} else {
    Write-Host 'Aviso: no se pudo generar el icono; se construye sin el.' -ForegroundColor Yellow
}

# --- 4. Construccion ---------------------------------------------------------
$pyiArgs = @(
    '-m', 'PyInstaller',
    '--onefile',
    '--console',
    '--clean',
    '--noconfirm',
    '--name', 'ParkingControl',
    '--distpath', 'dist',
    '--workpath', 'build\work',
    '--specpath', 'build'
)
if ($usarIcono) { $pyiArgs += @('--icon', $icono) }
$pyiArgs += 'lanzador.py'

Write-Host 'Construyendo ParkingControl.exe...' -ForegroundColor Cyan
& $python @pyiArgs
if ($LASTEXITCODE -ne 0) {
    Write-Host 'ERROR: fallo la construccion con PyInstaller.' -ForegroundColor Red
    exit 1
}

# --- 5. Copia a la raiz del proyecto -----------------------------------------
$origen = Join-Path $PSScriptRoot 'dist\ParkingControl.exe'
if (-not (Test-Path $origen)) {
    Write-Host 'ERROR: PyInstaller no genero dist\ParkingControl.exe.' -ForegroundColor Red
    exit 1
}
Copy-Item $origen -Destination $PSScriptRoot -Force

$destino = Join-Path $PSScriptRoot 'ParkingControl.exe'
$mb = [math]::Round((Get-Item $destino).Length / 1MB, 2)
Write-Host ''
Write-Host "Listo: $destino ($mb MB)" -ForegroundColor Green
Write-Host 'Haz doble clic para arrancar el servidor y abrir el navegador.' -ForegroundColor Green
