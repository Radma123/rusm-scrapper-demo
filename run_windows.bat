@echo off
chcp 65001 > nul
echo ===================================================
echo [Launcher] Проверка зависимостей и запуск проекта...
echo ===================================================

:: 1. Проверяем и устанавливаем requirements.txt
echo [1/3] Проверка пакетов из requirements.txt...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [Ошибка] Не удалось установить зависимости. Проверьте установку Python.
    pause
    exit /b
)

:: 2. Открываем локальный сайт в браузере с задержкой в 2 секунды
echo [2/3] Подготовка к открытию браузера...
start /b cmd /c "timeout /t 2 >nul && start http://localhost:6767"

:: 3. Запускаем основной скрипт
echo [3/3] Запуск сервера Uvicorn...
echo ---------------------------------------------------
python main.py

pause