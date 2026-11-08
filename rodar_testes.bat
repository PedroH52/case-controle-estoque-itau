@echo off
cd /d "%~dp0inventory_control"
echo ======================================================
echo    Executando Suite de Testes (pytest)
echo ======================================================
python -m pytest
pause
