FROM python:3.9-slim

WORKDIR /app

# Устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Явно ставим aiogram 3.x (на всякий случай)
RUN pip install aiogram==3.19.0

# Копируем код
COPY . .

CMD ["python", "bot.py"]