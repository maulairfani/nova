FROM python:3.12-slim

WORKDIR /app

COPY plus/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY common ./common
COPY plus .

EXPOSE 9002

CMD ["python", "server.py"]
