FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema operativo para los motores de base de datos
RUN apt-get update && apt-get install -y \
    postgresql-client \
    mariadb-client \
    curl \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Instalar herramientas para MongoDB
RUN curl -fsSL https://pgp.mongodb.com/server-7.0.asc | \
   gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg --dearmor && \
   echo "deb [ signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] http://repo.mongodb.org/apt/debian bookworm/mongodb-org/7.0 main" | tee /etc/apt/sources.list.d/mongodb-org-7.0.list && \
   apt-get update && apt-get install -y mongodb-database-tools && \
   rm -rf /var/lib/apt/lists/*

# Instalar mssql-tools18 para sqlcmd
RUN curl https://packages.microsoft.com/keys/microsoft.asc | tee /etc/apt/trusted.gpg.d/microsoft.asc && \
    curl https://packages.microsoft.com/config/debian/12/prod.list | tee /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && ACCEPT_EULA=Y apt-get install -y mssql-tools18 unixodbc-dev && \
    echo 'export PATH="$PATH:/opt/mssql-tools18/bin"' >> ~/.bashrc && \
    rm -rf /var/lib/apt/lists/*

ENV PATH="$PATH:/opt/mssql-tools18/bin"

# Instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código fuente
COPY src/ /app/src/

# Configurar variables de entorno y exponer puerto
ENV PYTHONPATH=/app
ENV TEMP_DIR=/tmp/safebridge_backups
EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
