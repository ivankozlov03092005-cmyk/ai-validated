FROM python:3.10-slim

# Установка системных зависимостей для EasyOCR
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Создаем папки для загрузок
RUN mkdir -p uploads/screenshots uploads/videos uploads/files _protected_uploads

# Открываем порт 7860 (стандарт для Hugging Face)
EXPOSE 7860

# Запускаем сервер
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]