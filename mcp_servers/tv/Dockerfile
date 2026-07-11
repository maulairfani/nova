FROM python:3.12-slim

WORKDIR /app

COPY tv/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY common ./common
COPY tv .

EXPOSE 9001

CMD ["python", "server.py"]
