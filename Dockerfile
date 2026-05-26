FROM node:20-bookworm

ENV NODE_ENV=production
ENV PYTHONUNBUFFERED=1
ENV PYTHON=/app/.venv/bin/python3
ENV CAMOUFOX_CACHE_DIR=/app/.cache/camoufox

WORKDIR /app

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
    python3 \
    python3-venv \
    python3-pip \
    ca-certificates \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcairo2 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libglib2.0-0 \
    libgtk-3-0 \
    libnss3 \
    libpango-1.0-0 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
  && rm -rf /var/lib/apt/lists/*

COPY requirements-scraper.txt ./
RUN python3 -m venv /app/.venv \
  && /app/.venv/bin/pip install --no-cache-dir --upgrade pip \
  && /app/.venv/bin/pip install --no-cache-dir -r requirements-scraper.txt \
  && /app/.venv/bin/python -m camoufox fetch

COPY . .

RUN chmod +x start.sh

EXPOSE 4173

CMD ["./start.sh"]
