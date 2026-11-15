FROM python:3.12-slim

WORKDIR /app
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend backend
COPY frontend frontend

WORKDIR /app/backend
# Railway inyecta $PORT en tiempo de ejecución
CMD ["sh", "-c", "gunicorn app:app --bind 0.0.0.0:${PORT:-8000} --workers 2 --timeout 60"]
