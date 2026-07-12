FROM python:3.12-slim

WORKDIR /app

COPY news/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY common ./common
COPY news .

EXPOSE 9003

CMD ["python", "server.py"]
