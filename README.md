# SafeBridge Telegram API - Documentación para IA (AI-Friendly Context)

## 🤖 AI Context: ¿Qué es este proyecto?

Este documento está diseñado específicamente para que cualquier Asistente de Inteligencia Artificial (IA) entienda de forma inmediata la naturaleza, estructura y propósito de este sistema. 

**SafeBridge Telegram API** es un **microservicio backend** escrito en Python utilizando **FastAPI**. Su objetivo principal es actuar como un "motor" o "core" que orquesta, genera y verifica copias de seguridad (backups) de múltiples motores de bases de datos.

Originalmente, esta lógica vivía en una aplicación de escritorio monolítica (Tauri/Rust). Ahora ha sido abstraída y reestructurada bajo los principios de **Clean Architecture** para ser consumida a través de una API REST.

---

## 🏗️ Motores de Base de Datos Soportados

El sistema está diseñado empleando el **Patrón Estrategia (Strategy Pattern)** para aislar la lógica de cada motor de base de datos. Actualmente soporta 4 motores mediante llamadas asíncronas (`asyncio.create_subprocess_exec`) a sus binarios nativos del sistema:
1. **MySQL / MariaDB** (vía `mysqldump`)
2. **PostgreSQL** (vía `pg_dump`)
3. **Microsoft SQL Server** (vía `sqlcmd`)
4. **MongoDB** (vía `mongodump`)

---

## ⚙️ ¿Cómo funciona el sistema? (Flujos paso a paso)

El sistema expone dos casos de uso principales (Endpoints):

### 1. Generación de Backups (`POST /api/v1/generar`)
*   **Entrada:** Un payload JSON (`BackupRequest`) validado estrictamente por Pydantic que incluye credenciales (host, puerto, usuario, contraseña), nombre de la base de datos y el tipo de motor.
*   **Proceso:**
    1. El router recibe la petición y delega al `BackupService`.
    2. El servicio selecciona la estrategia correcta (clase derivada de `BaseEngine`) según el motor solicitado.
    3. Se ejecuta el binario del sistema correspondiente (ej. `pg_dump`) de manera asíncrona, capturando el `stdout` y `stderr` para generar un historial de logs detallado.
    4. El archivo físico del volcado de la base de datos se guarda temporalmente en un directorio temporal del servidor.
*   **Salida:** La API retorna un binario físico (`FileResponse`) que el consumidor puede descargar. Los logs detallados y el estado final (`SUCCESS`/`FAILED`) se adjuntan en los Headers HTTP de la respuesta (`X-Backup-Logs`, `X-Backup-Status`). Finalmente, una tarea en background (`BackgroundTasks`) elimina el archivo del disco del servidor.

### 2. Verificación de Backups (`POST /api/v1/verificar`)
*   **Entrada:** Una subida de archivo multipart (`UploadFile`).
*   **Proceso:**
    1. El router intercepta el archivo y hace un rechazo en bloque (HTTP 400) si la extensión no es válida (solo acepta `.sql`, `.bak`, o `.bson`).
    2. Guarda el archivo localmente en chunks.
    3. El `VerifyService` delega la comprobación al motor asociado.
    4. **Mecanismo de verificación:** Dado que restaurar una base de datos real requiere credenciales y entornos de prueba desechables, este sistema emplea una validación "rápida e inteligente" de archivos. Para MySQL y Postgres, lee los últimos 256 bytes del archivo buscando firmas específicas (`Dump completed on` o `PostgreSQL database dump complete`). Para SQL Server y MongoDB, valida la integridad de tamaño.
*   **Salida:** Retorna un payload JSON indicando si el archivo está `"Sano"` o `"Corrupto"`, adjuntando todos los logs generados en el análisis.

---

## 📂 Arquitectura de Carpetas (Clean Architecture)

Si estás modificando o agregando código a este repositorio, respeta esta estructura:
*   `src/models/`: Contiene `schemas.py` donde se definen los modelos de Pydantic. **Toda entrada y salida de datos pasa por aquí.**
*   `src/core/`: Configuraciones de la app (`config.py`) manejando variables de entorno con `BaseSettings`, y excepciones personalizadas (`exceptions.py`) mapeadas a códigos HTTP.
*   `src/services/`: Toda la **lógica de negocio pura** (`backup_service.py`, `verify_service.py`).
*   `src/services/engines/`: Contiene la implementación del **Strategy Pattern**. `base.py` define la interfaz asíncrona, y los demás archivos contienen las ejecuciones de los comandos específicos de cada motor.
*   `src/api/v1/`: Los **Controladores (Routers)**. Estos archivos solo reciben peticiones HTTP, delegan a los servicios y construyen la respuesta HTTP. No deben contener lógica de comandos.
*   `Dockerfile`: Define un entorno `python:3.11-slim` donde se inyectan todas las dependencias del sistema operativo nativas (`postgresql-client`, `mssql-tools18`, etc.) requeridas por las estrategias.

---

## 🚀 ¿Hacia dónde va el sistema? (El Objetivo Final)

**Este backend es solo la mitad del proyecto final.**

El sistema fue diseñado para **desacoplarse y contenerizarse en Docker (VPS)**. Una vez en producción, este microservicio será consumido de forma exclusiva y automatizada por un **Bot de Telegram**.

El flujo final en el ecosistema será:
1. Un usuario autenticado le habla al Bot en Telegram.
2. El Bot de Telegram (que vive en su propio contenedor) hace peticiones asíncronas a esta FastAPI REST.
3. Esta FastAPI ejecutará el trabajo pesado de base de datos.
4. FastAPI retornará el archivo al Bot de Telegram.
5. El Bot de Telegram enviará el archivo físico directamente al chat del usuario y adjuntará los logs de operación.

---

## 🚀 Despliegue en VPS (Producción)

El repositorio ya está configurado para desplegarse fácilmente en cualquier VPS usando Docker Compose.

**Paso 1:** Clona o sube este repositorio a tu VPS.

**Paso 2:** Crea el archivo de variables de entorno.
```bash
cp .env.example .env
```
Edita el archivo `.env` (usando `nano .env`) y pon el token de tu bot provisto por BotFather:
```env
TELEGRAM_BOT_TOKEN=1234567890:AAH...
```

**Paso 3:** Levanta los servicios.
```bash
docker compose up -d
```
Esto creará y arrancará dos contenedores de forma paralela:
1. `api`: El motor encargado de realizar los volcados de bases de datos.
2. `bot`: El script de Python que escucha a Telegram y orquesta la comunicación con la API interna.
