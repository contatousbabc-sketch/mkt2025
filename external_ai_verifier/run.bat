@echo off
setlocal enabledelayedexpansion

REM ARQV30 Enhanced v3.0 - External AI Verifier Execution Script
REM Script de execução do módulo independente

echo ========================================
echo ARQV30 Enhanced v3.0 - External AI Verifier
echo Execução do Módulo de Verificação por IA
echo ========================================
echo.

REM Muda para o diretório do script
pushd "%~dp0"

REM Verifica se o ambiente virtual existe
if not exist "ai_verifier_env" (
    echo ❌ ERRO: Ambiente virtual não encontrado!
    echo Execute install.bat primeiro para configurar o módulo.
    pause
    popd
    exit /b 1
)

REM Ativa ambiente virtual
echo 🔄 Ativando ambiente virtual...
call ai_verifier_env\Scripts\activate.bat
if errorlevel 1 (
    echo ❌ ERRO: Falha ao ativar ambiente virtual!
    pause
    popd
    exit /b 1
)

REM Cria diretórios necessários
if not exist "output" mkdir output
if not exist "logs" mkdir logs
if not exist "temp" mkdir temp

REM Verifica se existe arquivo de dados de entrada
set INPUT_FILE=input_data.json
if exist "%INPUT_FILE%" (
    echo ✅ Arquivo de entrada encontrado: %INPUT_FILE%
) else (
    echo ⚠️ Arquivo de entrada não encontrado: %INPUT_FILE%
    echo Criando arquivo de exemplo...
    
    echo { > %INPUT_FILE%
    echo   "items": [ >> %INPUT_FILE%
    echo     { >> %INPUT_FILE%
    echo       "id": "exemplo1", >> %INPUT_FILE%
    echo       "content": "Este é um exemplo de conteúdo para análise de IA. O texto deve ser claro e objetivo.", >> %INPUT_FILE%
    echo       "title": "Título de Exemplo", >> %INPUT_FILE%
    echo       "source": "fonte_exemplo.com" >> %INPUT_FILE%
    echo     }, >> %INPUT_FILE%
    echo     { >> %INPUT_FILE%
    echo       "id": "exemplo2", >> %INPUT_FILE%
    echo       "content": "Especialistas afirmam que este texto contém padrões suspeitos de desinformação que sempre enganam todos.", >> %INPUT_FILE%
    echo       "title": "Título Suspeito", >> %INPUT_FILE%
    echo       "source": "fonte_duvidosa.com" >> %INPUT_FILE%
    echo     } >> %INPUT_FILE%
    echo   ], >> %INPUT_FILE%
    echo   "context": { >> %INPUT_FILE%
    echo     "topic": "exemplo", >> %INPUT_FILE%
    echo     "source_analysis": true >> %INPUT_FILE%
    echo   } >> %INPUT_FILE%
    echo } >> %INPUT_FILE%
    
    echo ✅ Arquivo de exemplo criado: %INPUT_FILE%
    echo Edite este arquivo com seus dados reais antes da execução.
)

echo.
echo 🚀 Iniciando processamento...
echo ⏱️ Timestamp: %date% %time%
echo.

REM Executa o CLI Python
python -u src\cli_run.py
set CLI_EXIT_CODE=%ERRORLEVEL%

echo.
if %CLI_EXIT_CODE% EQU 0 (
    echo ⏹️ Processamento finalizado com sucesso.
    echo 📊 Consulte o arquivo de resultado em output/ para detalhes.
) else (
    echo ❌ Processamento finalizado com erros. Código de saída: %CLI_EXIT_CODE%
)
echo.

popd
endlocal

pause
exit /b %CLI_EXIT_CODE%