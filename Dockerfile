FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOME=/home/app

WORKDIR /app

RUN addgroup --system --gid 10001 app && \
    adduser --system --uid 10001 --home /home/app --ingroup app app

COPY requirements.txt .
RUN pip install --no-cache-dir --requirement requirements.txt

COPY --chown=app:app app ./app

USER 10001:10001

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--threads", "2", "--access-logfile", "-", "app:create_app()"]
