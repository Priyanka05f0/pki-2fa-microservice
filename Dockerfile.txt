FROM python:3.11-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --prefix=/install --no-warn-script-location --no-cache-dir -r requirements.txt
COPY . .

FROM python:3.11-slim AS runtime
ENV TZ=UTC
RUN apt-get update && \
    apt-get install -y --no-install-recommends cron tzdata && \
    ln -snf /usr/share/zoneinfo/Etc/UTC /etc/localtime && \
    echo "Etc/UTC" > /etc/timezone && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY --from=builder /install /usr/local
COPY --from=builder /app /app

RUN mkdir -p /data /cron && chmod 755 /data /cron
RUN chmod 0644 /app/cron/2fa-cron && crontab /app/cron/2fa-cron

EXPOSE 8080
CMD ["sh", "-c", "cron && uvicorn main:app --host 0.0.0.0 --port 8080"]
