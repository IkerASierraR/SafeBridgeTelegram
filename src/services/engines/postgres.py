import asyncio
import os
from typing import Tuple, List
from src.services.engines.base import BaseEngine
from src.models.schemas import BackupRequest

class PostgresEngine(BaseEngine):
    async def backup(self, request: BackupRequest, file_path: str) -> Tuple[bool, List[str]]:
        logs = []
        env = os.environ.copy()
        env["PGPASSWORD"] = request.contrasena
        
        cmd = [
            "pg_dump",
            "-h", request.host,
            "-p", str(request.puerto),
            "-U", request.usuario,
            "-F", "p",  # Formato plano (sql)
            "-f", file_path,
            request.nombre_bd
        ]
        
        logs.append(f"Ejecutando backup PostgreSQL para {request.nombre_bd}")
        process = await asyncio.create_subprocess_exec(
            *cmd,
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            err = stderr.decode().strip()
            logs.append(f"Error pg_dump: {err}")
            return False, logs
            
        logs.append("Backup generado con éxito")
        return True, logs

    async def verify(self, file_path: str, request: BackupRequest = None) -> Tuple[bool, List[str]]:
        logs = ["Iniciando verificación de backup de PostgreSQL"]
        
        try:
            with open(file_path, "rb") as f:
                f.seek(0, 2)
                size = f.tell()
                read_size = 256 if size > 256 else size
                f.seek(-read_size, 2)
                end_content = f.read().decode(errors="ignore")
                
                if "PostgreSQL database dump complete" in end_content:
                    logs.append("Verificación exitosa: Se encontró firma de pg_dump válida.")
                    return True, logs
                else:
                    logs.append("Advertencia: No se encontró la firma de pg_dump al final del archivo.")
                    return False, logs
        except Exception as e:
            logs.append(f"Error al verificar archivo: {str(e)}")
            return False, logs
