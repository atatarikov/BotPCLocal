# Используем официальный образ Python версии 3.10
FROM python:3.10-slim-buster

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы requirements.txt для установки зависимостей
COPY requirements.txt .

# Устанавливаем зависимости из pip
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходники нашего проекта
COPY . .

# Запускаем сервер на порту 5001
# CMD ["flask", "run", "--host=0.0.0.0"]

# Запускаем Gunicorn вместо Flask (4 воркера, порт 5000)
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "app:app"]