#Dockerfile

FROM zauberzeug/zauberzeug/nicegui:latest

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY wheel_app.py .

EXPOSE 8080

CMD ["python", "wheel_app.py"]