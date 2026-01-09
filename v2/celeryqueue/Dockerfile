FROM python:3.12

WORKDIR /app

# Copia i requirements e installa
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia tutto il resto del codice
COPY . .

# Non mettiamo CMD qui, lo definiremo nel docker-compose