FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN addgroup --system app && adduser --system --ingroup app --home /home/app app
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --requirement requirements.txt

COPY main.py prompt.py rag.py settings.py ./
RUN chown -R app:app /app /home/app

USER app
EXPOSE 8088

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8088/readiness', timeout=3)"

CMD ["python", "main.py"]
