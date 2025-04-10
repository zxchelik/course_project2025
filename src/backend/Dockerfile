# Этап сборки wheel-файлов
FROM python:3.11-slim-bullseye AS build

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app

COPY ../../requirements.txt .

# Устанавливаем зависимости для сборки расширений, нужные aiohttp и др.
RUN apt update && \
    apt install -y gcc libffi-dev libssl-dev build-essential && \
    pip install --no-cache-dir pip wheel && \
    pip wheel --no-cache-dir --wheel-dir /opt/wheels -r requirements.txt

# Финальный минимальный образ
FROM python:3.11-slim-bullseye AS final

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Установка только wheel-файлов без компиляции
COPY --from=build /opt/wheels /opt/wheels
RUN pip install --no-cache-dir /opt/wheels/* && rm -rf /opt/wheels

# Копируем весь исходный код
COPY src/backend .

EXPOSE ${WEBHOOK_PORT}
CMD ["python", "app.py"]
