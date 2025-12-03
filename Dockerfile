# Stage 1: builder (install dependencies)
FROM python:3.11-slim AS builder
WORKDIR /app

COPY requirements.txt .
RUN pip install --prefix=/install --no-warn-script-location --no-cache-dir -r requirements.txt

COPY . .

# Stage 2: runtime
FROM python:3.11-slim AS runtime
ENV TZ=UTC

# Install cron, timezone data, and procps (fixes "ps: command not found")
RUN apt-get update && \
    apt-get install -y --no-install-recommends cron tzdata procps && \
    ln -snf /usr/share/zoneinfo/Etc/UTC /etc/localtime && \
    echo "Etc/UTC" > /etc/timezone && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy installed Python packages and app code
COPY --from=builder /install /usr/local
COPY --from=builder /app /app

# Ensure directories exist and permissions are correct
RUN mkdir -p /data /cron /var/log && chmod 755 /data /cron /var/log

# Install cron job file
COPY cron/docker-2fa-cron /etc/cron.d/docker-2fa-cron
RUN chmod 0644 /etc/cron.d/docker-2fa-cron

# Copy entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose application port
EXPOSE 8080

# Start cron and the FastAPI service
ENTRYPOINT ["/entrypoint.sh"]
