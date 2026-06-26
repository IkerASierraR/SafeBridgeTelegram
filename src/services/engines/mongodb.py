import asyncio
import os
from typing import Tuple, List
from src.services.engines.base import BaseEngine
from src.models.schemas import BackupRequest

class MongoDBEngine(BaseEngine):
    async def backup(self, request: BackupRequest, file_path: str) -> Tuple[bool, List[str]]:
        logs = []
        
        mongo_uri = f"mongodb://{request.usuario}:{request.contrasena}@{request.host}:{request.puerto}/{request.nombre_bd}"
        
        cmd = [
            "mongodump",
            "--uri", mongo_uri,
            f"--archive={file_path}"
        ]
        
        logs.append(f"Ejecutando backup MongoDB para {request.nombre_bd}")
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            err = stderr.decode().strip()
            logs.append(f"Error mongodump: {err}")
            return False, logs
            
        logs.append("Backup generado con éxito")
        return True, logs

    async def verify(self, file_path: str, request: BackupRequest = None) -> Tuple[bool, List[str]]:
        logs = ["Iniciando verificación de backup de MongoDB"]
        
        try:
            size = os.path.getsize(file_path)
            if size == 0:
                logs.append("El archivo de backup está vacío (0 bytes).")
                return False, logs
            
            logs.append("Verificación exitosa: Archivo generado correctamente (validación de tamaño).")
            return True, logs
        except Exception as e:
            logs.append(f"Error al verificar archivo: {str(e)}")
            return False, logs
