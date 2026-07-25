FROM python:3.12-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


COPY portfolio_agent/ ./portfolio_agent/
COPY main.py .

RUN useradd -m appuser
USER appuser


ENV PORT=8080
EXPOSE 8080

CMD exec uvicorn main:app --host 0.0.0.0 --port $PORT