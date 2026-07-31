FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN addgroup --system app && adduser --system --ingroup app --home /home/app app
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --requirement requirements.txt

COPY __init__.py chunking.py extractors.py index_schema.py ingest.py settings.py ./
RUN chown -R app:app /app /home/app

USER app
ENTRYPOINT ["python", "ingest.py"]
