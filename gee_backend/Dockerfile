FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY goes_tiles.py .
ENV PORT=8090
EXPOSE 8090
CMD ["sh", "-c", "uvicorn goes_tiles:app --host 0.0.0.0 --port ${PORT}"]
