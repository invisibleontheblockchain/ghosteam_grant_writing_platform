# =========================================================
# Stage 1: Build the React Frontend
# =========================================================
FROM node:18-alpine AS frontend-build

WORKDIR /app/frontend

# Copy package files first for better Docker layer caching
COPY frontend/package.json frontend/package-lock.json* ./

# Install dependencies
RUN npm ci --production=false

# Copy the rest of the frontend source
COPY frontend/ ./

# Build the production bundle
RUN npm run build


# =========================================================
# Stage 2: Python Backend + Serve Built Frontend
# =========================================================
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements-deploy.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source code
COPY app.py ./
COPY engines/ ./engines/
COPY services/ ./services/
COPY config/ ./config/
COPY parsers/ ./parsers/
COPY vector_store/ ./vector_store/
COPY winning_grants/ ./winning_grants/

# Copy the SAFE knowledge base documents
COPY SAFE_*.md ./
COPY THREE_TIER_*.md ./

# Copy built React frontend from Stage 1
COPY --from=frontend-build /app/frontend/dist ./static_build

# Create directories that the app expects
RUN mkdir -p uploads generated_grants learning_data vector_db logs

# Set environment variables
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Railway sets PORT dynamically
ENV PORT=5000

# Expose the port
EXPOSE $PORT

# Run with gunicorn for production
CMD gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 --access-logfile - app:app
