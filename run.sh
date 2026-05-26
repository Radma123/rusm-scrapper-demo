#!/bin/bash

# Проверка и обновление из git
git fetch origin

LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/master)

if [ "$LOCAL" != "$REMOTE" ]; then
    echo "📦 Найдено обновление, обновляю..."
    git pull origin master
fi

# Запуск приложения
python main.py "$@"
