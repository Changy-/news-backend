FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Use 8080 as default (common for Cloud Run), but overrideable via $PORT
ENV PORT=8080

CMD uvicorn main:app --host 0.0.0.0 --port $PORT
