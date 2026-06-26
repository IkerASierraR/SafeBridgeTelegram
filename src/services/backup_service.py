import os
from datetime import datetime
from src.models.schemas import BackupRequest
from src.services.engines import get_engine_strategy
from src.core.config import settings

class BackupService:
    @staticmethod
    async def generate_backup(request: BackupRequest) -> tuple[str, list[str]]:
        engine_strategy = get_engine_strategy(request.motor)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        ext = {
            "mysql": "sql",
            "postgresql": "sql",
            "sqlserver": "bak",
            "mongodb": "bson"
        }.get(request.motor.value, "bak")
        
        file_name = f"{request.nombre_bd}_{timestamp}.{ext}"
        file_path = os.path.join(settings.TEMP_DIR, file_name)
        
        success, logs = await engine_strategy.backup(request, file_path)
        
        if success:
            verify_success, verify_logs = await engine_strategy.verify(file_path, request)
            logs.extend(verify_logs)
            if not verify_success:
                logs.append("La verificación post-backup falló.")
        else:
            logs.append("El proceso de backup falló.")
            
        return file_path, logs
