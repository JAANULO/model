FROM python:3.11-slim

WORKDIR /app

# zależności systemowe wymagane przez pdfplumber
RUN apt-get update && apt-get install -y \
    libpoppler-cpp-dev \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# zależności Python (bez torch)
COPY v2/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# kopiuj projekt
COPY v2/ .

# utwórz wymagane foldery
RUN mkdir -p logs data

EXPOSE 5000

CMD ["python", "app.py"]
