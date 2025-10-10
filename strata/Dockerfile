FROM python:3.11-slim

WORKDIR /app

COPY strata/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY strata /app/strata

ENV PORT=8080
EXPOSE 8080

CMD ["python", "-m", "uvicorn", "strata.main:app", "--host", "0.0.0.0", "--port", "8080"]