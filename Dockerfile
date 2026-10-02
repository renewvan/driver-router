FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY node_router/ node_router/

ENTRYPOINT ["python", "-m", "node_router.main"]
