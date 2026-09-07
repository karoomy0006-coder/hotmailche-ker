# Email Auditor Pro — Docker Deployment
FROM python:3.11-slim

WORKDIR /app

# Install system deps for aiodns
RUN apt-get update && apt-get install -y --no-install-recommends gcc libffi-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Persist data & results
VOLUME ["/app/data", "/app/results"]

ENV PYTHONUNBUFFERED=1
CMD ["python", "bot.py"]
