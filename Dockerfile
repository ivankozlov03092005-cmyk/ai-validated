FROM python:3.10-slim

# Установка системных зависимостей
# Заменили libgl1-mesa-glx на libgl1 (актуально для новых версий Debian)
# Добавили libglib2.0-0 и libsm6 для работы OpenCV/EasyOCR
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgl1 \
    git \
    wget \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копируем требования и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . .

# Создаем необходимые папки
RUN mkdir -p uploads/screenshots uploads/videos uploads/files _protected_uploads

# Открываем порт
EXPOSE 7860

# Команда запуска
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]