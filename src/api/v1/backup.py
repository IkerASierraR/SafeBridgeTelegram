from fastapi import APIRouter, BackgroundTasks
from fastapi.responses import FileResponse
from src.models.schemas import BackupRequest
from src.services.backup_service import BackupService
from src.core.exceptions import BackupException
import os
import json

router = APIRouter()

def remove_file(path: str):
    try:
        os.remove(path)
    except Exception:
        pass

@router.post("/generar", response_class=FileResponse)
async def generar_backup(request: BackupRequest, background_tasks: BackgroundTasks):
    """
    Genera un backup en base a los datos proporcionados.
    Retorna el archivo físico. Los logs y el estado se devuelven en custom headers.
    El archivo se elimina automáticamente del servidor después de enviarlo.
    """
    file_path, logs = await BackupService.generate_backup(request)
    
    if not os.path.exists(file_path):
        raise BackupException("El archivo de backup no fue generado correctamente.")
        
    # Agregamos tarea en background para limpiar el archivo una vez enviado
    background_tasks.add_task(remove_file, file_path)
    
    # Preparamos un string JSON para los headers y aseguramos que sea ascii-safe
    logs_json = json.dumps(logs)
    safe_logs = logs_json.encode('utf-8').decode('unicode_escape')
    
    headers = {
        "X-Backup-Logs": "Consulta la respuesta o envuelve esto en multipart",
        # Custom header flag para éxito
        "X-Backup-Status": "SUCCESS" if "falló" not in logs[-1].lower() else "FAILED"
    }
    
    return FileResponse(
        path=file_path, 
        filename=os.path.basename(file_path),
        headers=headers,
        media_type='application/octet-stream'
    )
