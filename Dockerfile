# Используем официальный Python-образ
FROM python:3.11-slim

# Обновляем пакеты и ставим зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Создаём рабочую директорию внутри контейнера
WORKDIR /app

# Копируем зависимости
COPY requirements.txt .

# Устанавливаем зависимости Python
RUN pip install --no-cache-dir -r requirements.txt

# Копируем всё остальное внутрь контейнера
COPY . .

# Запуск основного скрипта
CMD ["python", "main.py"]
