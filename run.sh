#!/bin/bash

# Переходим в директорию, где лежит сам этот файлик
cd "$(dirname "$0")"

echo "==================================================="
echo "[Launcher] Проверка окружения и запуск проекта..."
echo "==================================================="

# 1. Проверяем и создаем виртуальное окружение
if [ ! -d ".venv" ]; then
    echo "[1/5] Папка .venv не найдена. Создаем изолированное окружение..."
    python3 -m venv .venv
    if [ $? -ne 0 ]; then
        echo "[Ошибка] Не удалось создать виртуальное окружение. Проверьте установку python3."
        exit 1
    fi
else
    echo "[1/5] Виртуальное окружение .venv уже существует."
fi

# 2. Активируем venv
echo "[2/5] Активация виртуального окружения..."
source .venv/bin/activate

# 3. Обновляем pip и ставим пакеты внутри venv
echo "[3/5] Проверка и установка пакетов из requirements.txt..."
pip install --upgrade pip
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "[Ошибка] Не удалось установить зависимости внутрь venv."
    deactivate
    exit 1
fi

# 4. Проверка обновлений из git
echo "[4/5] Проверка обновлений..."
git fetch origin > /dev/null 2>&1
LOCAL=$(git rev-parse HEAD 2>/dev/null || echo "local")
REMOTE=$(git rev-parse origin/master 2>/dev/null || echo "local")

if [ "$LOCAL" != "local" ] && [ "$REMOTE" != "local" ] && [ "$LOCAL" != "$REMOTE" ]; then
    echo "[Обновление] Найдено обновление, обновляю..."
    git pull origin master
    echo "[Обновление] Завершено! Переустанавливаю зависимости..."
    pip install -r requirements.txt > /dev/null 2>&1
fi

# 5. Открываем браузер через 2 секунды в фоновом режиме (определяем OS)
echo "[5/5] Подготовка к открытию браузера..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    (sleep 2 && open "http://localhost:6767") &
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    (sleep 2 && (xdg-open "http://localhost:6767" || python3 -m webbrowser "http://localhost:6767")) &
fi

# 6. Запускаем проект через python из виртуального окружения
echo " Запуск сервера Uvicorn..."
echo "---------------------------------------------------"
python3 main.py

# Деактивация окружения при закрытии сервера
deactivate
