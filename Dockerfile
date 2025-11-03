# Multi-runtime container: Node + Python for Railway

FROM node:20-bookworm

# Install Python 3 and venv
RUN apt-get update -y \
    && apt-get install -y --no-install-recommends python3 python3-venv python3-pip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy backend requirements first for better caching and create venv
COPY backend/requirements.txt backend/requirements.txt
RUN python3 -m venv backend/venv \
    && backend/venv/bin/pip install --upgrade pip \
    && backend/venv/bin/pip install -r backend/requirements.txt

# Install frontend dependencies
COPY frontend/package*.json frontend/
RUN cd frontend \
    && npm ci --omit=dev || npm install --production

# Copy the rest of the repo
COPY . .

ENV NODE_ENV=production
ENV PORT=3000
EXPOSE 3000

# Start the Node server; it will spawn the Python process from the created venv
CMD ["node", "frontend/server.js"]

