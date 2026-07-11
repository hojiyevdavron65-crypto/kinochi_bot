FROM python:3.11-slim

WORKDIR /app

# ffmpeg — video preview kesish uchun
# postgresql-client — pg_dump orqali kunlik backup olish uchun
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg postgresql-client && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

CMD ["python", "app.py"]