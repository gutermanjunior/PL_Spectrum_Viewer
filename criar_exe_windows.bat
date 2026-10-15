@echo off
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
  set "PY=.venv\Scripts\python.exe"
) else (
  set "PY=py -3"
)
%PY% -m pip install -r requirements.txt pyinstaller
if errorlevel 1 exit /b 1
%PY% -m PyInstaller --noconfirm --clean --windowed --name "PL_Spectrum_Viewer" main.py
if errorlevel 1 (
  echo Falha no empacotamento.
  pause
  exit /b 1
)
echo O executavel estara na pasta dist\PL_Spectrum_Viewer\
pause
