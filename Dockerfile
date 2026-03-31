FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    procps \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN useradd -m -u 1000 userdocker

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bot/ ./bot/

USER userdocker

EXPOSE 8080
CMD ["python", "-m", "bot.main"]
