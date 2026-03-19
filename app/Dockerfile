FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt
run pip install --no-cache-dir -r requirements.txt

COPY src/.gitkeep

EXPOSE 80

CMD ["python", "webhook_handler.py"