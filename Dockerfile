# Stage 1: builder (install dependencies)
FROM python:3.11-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --prefix=/install --no-warn-script-location --no-cache-dir -r requirements.txt
COPY . .

# Stage 2: runtime
FROM python:3.11-slim AS runtime
ENV TZ=UTC

# Install cron and timezone data, cleanup apt cache
RUN apt-get update && \
    apt-get install -y --no-install-recommends cron tzdata && \
    ln -snf /usr/share/zoneinfo/Etc/UTC /etc/localtime && \
    echo "Etc/UTC" > /etc/timezone && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy installed Python packages and app code from builder
COPY --from=builder /install /usr/local
COPY --from=builder /app /app

# Ensure directories exist and permissions are sane
RUN mkdir -p /data /cron /var/log && chmod 755 /data /cron /var/log

# Install cron job file into /etc/cron.d (preferred)
# NOTE: we will copy a cron file named docker-2fa-cron (created in repo)
COPY cron/docker-2fa-cron /etc/cron.d/docker-2fa-cron
RUN chmod 0644 /etc/cron.d/docker-2fa-cron

# Provide an entrypoint script that starts cron then the app
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose port and user (keep root for cron simplicity)
EXPOSE 8080

# Use the entrypoint script to start cron + uvicorn (it will exec uvicorn)
ENTRYPOINT ["/entrypoint.sh"]
