# Backend Dockerfile
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR $WORKDIR

# Install python dependencies
COPY requirements.txt $WORKDIR/
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn daphne

# Copy project
COPY . $WORKDIR/

# Entrypoint script
COPY ./entrypoint.sh $WORKDIR/
RUN chmod +x $WORKDIR/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
