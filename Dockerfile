FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema operativo para los motores de base de datos
RUN apt-get update && apt-get install -y \
    postgresql-client \
    mariadb-client \
    curl \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Instalar herramientas para MongoDB desde binarios precompilados (Evita error de firma SHA1 de Debian Trixie)
RUN curl -fsSL -o mongodb-tools.tgz https://fastdl.mongodb.org/tools/db/mongodb-database-tools-debian12-x86_64-100.9.4.tgz && \
    tar -zxvf mongodb-tools.tgz && \
    cp mongodb-database-tools-debian12-x86_64-100.9.4/bin/* /usr/local/bin/ && \
    rm -rf mongodb-tools.tgz mongodb-database-tools-debian12-x86_64-100.9.4

# Instalar mssql-tools18 para sqlcmd
RUN curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg && \
    curl -fsSL https://packages.microsoft.com/config/debian/12/prod.list | tee /etc/apt/sources.list.d/mssql-release.list && \
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
