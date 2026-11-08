@echo off
title API de Controle de Estoque - Itau Case
cd /d "%~dp0inventory_control"

echo ====================================================================
echo      INICIANDO API DE CONTROLE DE ESTOQUE (CASE ITAU)
echo ====================================================================
echo.
echo  1. Iniciando servidor HTTP local (FastAPI / Uvicorn)...
echo  2. O seu navegador padrao abrira automaticamente no Swagger:
echo     http://127.0.0.1:8000/docs
echo.
echo  Para encerrar o servidor a qualquer momento, pressione CTRL+C nesta tela.
echo ====================================================================
echo.

python run.py

pause
