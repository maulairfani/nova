FROM python:3.12-slim

WORKDIR /app

COPY shared/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY common ./common
COPY shared .

EXPOSE 9004

CMD ["python", "server.py"]
