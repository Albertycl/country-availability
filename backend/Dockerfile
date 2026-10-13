FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 5030
CMD ["sh", "-c", "python init_db.py && python waitress_server.py"]
