# Imagen base estable para Python 3.9
FROM python:3.9-slim

# Evita prompts y cache de pip
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    WEBSITES_PORT=8080 \
    PADDLE_HOME=/home/site/.paddleocr

# Dependencias del sistema para OpenCV y friends
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 libsm6 libxext6 libxrender1 libgl1 libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Carpeta de la app
WORKDIR /app

# Primero dependencias (cache más eficiente)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Exponer puerto del uvicorn
EXPOSE 8080

# Arranque
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
