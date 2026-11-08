@echo off
echo ====================================================================
echo   Liberando a porta 8000 (encerrando processos anteriores)...
echo ====================================================================
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000') do taskkill /f /pid %%a 2>nul
echo.
echo Porta 8000 liberada com sucesso!
echo Agora voce pode clicar em CLIQUE_AQUI_PARA_INICIAR.bat novamente.
echo ====================================================================
pause
