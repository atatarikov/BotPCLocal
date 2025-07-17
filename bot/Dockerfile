# Используем официальную сборку Python с минималистичным дистрибутивом Debian Buster
FROM python:3.10-slim-buster

# Объявляем переменную среды для предотвращения кеширования pyc файлов
ENV PYTHONDONTWRITEBYTECODE=1

# Включаем режим буферизации вывода
ENV PYTHONUNBUFFERED=1

# Настраиваем рабочую директорию
WORKDIR /usr/src/app

# Копируем requirements.txt и устанавливаем зависимости
COPY ./requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем остальные файлы приложения
COPY . .

# Определяем точку входа для запуска бота
CMD ["python", "./main.py"]