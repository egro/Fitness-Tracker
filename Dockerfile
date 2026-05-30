FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

COPY . .

RUN mkdir -p /app/data /app/media && \
    python manage.py collectstatic --noinput

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
