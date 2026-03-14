FROM python:3.12-alpine
WORKDIR /app
RUN pip install fastapi uvicorn python-multipart --no-cache-dir
COPY main.py .
COPY static/ ./static/
RUN mkdir -p /data
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
