"""
Cliente HTTP asíncrono para comunicarse con la API interna de SafeBridge.
Centraliza todas las peticiones HTTP y el manejo de errores de red.
"""
import os
import logging
import httpx
import tempfile
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

API_URL = os.getenv("API_URL", "http://api:8000/api/v1")

# Timeout generoso: los backups grandes pueden tardar varios minutos
TIMEOUT = httpx.Timeout(timeout=600.0, connect=15.0)


async def solicitar_backup(payload: dict) -> Tuple[bool, str, Optional[str], Optional[str]]:
    """
    Envía la solicitud de backup a la API.
    
    Returns:
        Tuple: (exito, mensaje, ruta_archivo_temporal, nombre_archivo)
    """
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(f"{API_URL}/generar", json=payload)

            if response.status_code == 200:
                # Extraer nombre del archivo de los headers
                content_disposition = response.headers.get("content-disposition", "")
                filename = "backup.sql"
                if "filename=" in content_disposition:
                    filename = content_disposition.split("filename=")[1].strip('"')

                # Guardar el archivo en un temporal
                suffix = f"_{filename}"
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    tmp.write(response.content)
                    tmp_path = tmp.name

                return True, "Backup generado exitosamente.", tmp_path, filename

            elif response.status_code == 422:
                # Error de validación de Pydantic
                detail = response.json().get("detail", "Datos inválidos.")
                return False, f"⚠️ Error de validación:\n{detail}", None, None

            elif response.status_code == 500:
                detail = response.json().get("detail", "Error interno del servidor.")
                return False, f"❌ Error del servidor:\n{detail}", None, None

            else:
                return False, f"❌ Error inesperado (HTTP {response.status_code}):\n{response.text}", None, None

    except httpx.ConnectError:
        logger.error("No se pudo conectar a la API.")
        return False, "🔌 No pude conectarme a la API. Verifica que el servicio esté corriendo.", None, None
    except httpx.TimeoutException:
        logger.error("Timeout al contactar la API.")
        return False, "⏳ La API tardó demasiado en responder. El backup puede ser muy pesado.", None, None
    except Exception as e:
        logger.error(f"Error inesperado en solicitar_backup: {e}")
        return False, f"💥 Error inesperado: {str(e)}", None, None


async def solicitar_verificacion(file_path: str, filename: str) -> Tuple[bool, str, list]:
    """
    Envía un archivo de backup a la API para su verificación.
    
    Returns:
        Tuple: (exito, status_text, logs)
    """
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            with open(file_path, "rb") as f:
                files = {"file": (filename, f, "application/octet-stream")}
                response = await client.post(f"{API_URL}/verificar", files=files)

            if response.status_code == 200:
                data = response.json()
                status = data.get("status", "Desconocido")
                logs = data.get("logs", [])
                return True, status, logs

            elif response.status_code == 422:
                detail = response.json().get("detail", "Archivo inválido.")
                return False, f"⚠️ Error de validación: {detail}", []

            elif response.status_code == 500:
                detail = response.json().get("detail", "Error interno.")
                return False, f"❌ Error del servidor: {detail}", []

            else:
                return False, f"❌ Error inesperado (HTTP {response.status_code})", []

    except httpx.ConnectError:
        return False, "🔌 No pude conectarme a la API. Verifica que el servicio esté corriendo.", []
    except httpx.TimeoutException:
        return False, "⏳ La API tardó demasiado. El archivo puede ser muy pesado.", []
    except Exception as e:
        logger.error(f"Error inesperado en solicitar_verificacion: {e}")
        return False, f"💥 Error inesperado: {str(e)}", []
