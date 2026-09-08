FROM python:3.12-slim
WORKDIR /app
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt
COPY backend/app.py /app/backend/app.py
COPY frontend /app/frontend
RUN mkdir -p /app/storage
EXPOSE 8000
CMD ["uvicorn","backend.app:app","--host","0.0.0.0","--port","8000"]
