FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATA_FILE=/var/lib/backend_data/tasks.json

WORKDIR /app

COPY app.py /app/app.py

RUN mkdir -p /var/lib/backend_data

VOLUME ["/var/lib/backend_data"]

EXPOSE 5000

HEALTHCHECK --interval=10s --timeout=3s --start-period=3s --retries=3 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/health', timeout=2)"

CMD ["python3", "app.py"]
