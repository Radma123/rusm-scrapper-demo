@echo off
chcp 65001 > nul
echo ===================================================
echo [Launcher] Проверка окружения и запуск проекта...
echo ===================================================

:: 1. Проверяем и создаем виртуальное окружение
if not exist ".venv" (
    echo [1/4] Папка .venv не найдена. Создаем изолированное окружение...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo [Ошибка] Не удалось создать виртуальное окружение. Проверьте установку Python.
        pause
        exit /b
    )
) else (
    echo [1/4] Виртуальное окружение .venv уже существует.
)

:: 2. Активируем venv
echo [2/4] Активация виртуального окружения...
call .venv\Scripts\activate.bat

:: 3. Обновляем pip и ставим пакеты внутри venv
echo [3/4] Проверка и установка пакетов из requirements.txt...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [Ошибка] Не удалось установить зависимости внутрь venv.
    pause
    exit /b
)

:: 4. Проверка обновлений из git
echo [4/4] Проверка обновлений...
git fetch origin > nul 2>&1
for /f %%i in ('git rev-parse HEAD') do set LOCAL=%%i
for /f %%i in ('git rev-parse origin/master') do set REMOTE=%%i

if not "%LOCAL%"=="%REMOTE%" (
    echo [Обновление] Найдено обновление, обновляю...
    git pull origin master
    echo [Обновление] Завершено! Перезапускаю...
    python -m pip install -r requirements.txt > nul 2>&1
)

:: 5. Открываем локальный сайт в браузере с задержкой в 2 секунды
echo [5/5] Подготовка к открытию браузера...
start /b cmd /c "timeout /t 2 >nul && start http://localhost:6767"

:: 6. Запускаем основной скрипт
echo  Запуск сервера Uvicorn...
echo ---------------------------------------------------
python main.py

pause