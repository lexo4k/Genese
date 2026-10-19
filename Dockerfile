FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=10000 GENESE_HOST=0.0.0.0 GENESE_DB_PATH=/data/genese_wallet.sqlite3
WORKDIR /app
RUN useradd --system --uid 10001 --create-home appuser && mkdir -p /data && chown -R appuser:appuser /app /data
COPY --chown=appuser:appuser . .
USER appuser
EXPOSE 10000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 CMD python -c "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:'+os.getenv('PORT','10000')+'/health',timeout=4).read()"
CMD ["python", "wallet_api.py"]
