import os
from src.models.schemas import EngineEnum
from src.services.engines import get_engine_strategy

class VerifyService:
    @staticmethod
    async def verify_uploaded_file(file_path: str, file_name: str) -> tuple[bool, list[str]]:
        ext = file_name.split('.')[-1].lower()
        
        # Determinar el motor en base a la extensión, ya que no se pasa explicitamente
        engine = None
        if ext == "sql":
            # Puede ser MySQL o Postgres, probamos con MySQL ya que la verificación de Postgres 
            # también busca una firma y no fallará catastróficamente si leemos el final del archivo
            engine = EngineEnum.mysql 
            # Sin embargo, lo ideal sería intentar ambos o pedir el motor en el endpoint
            # Por ahora el diseño pide "validación estricta de extensiones permitidas según los 4 motores"
            # Vamos a intentar detectar cuál de las firmas está
        elif ext == "bak":
            engine = EngineEnum.sqlserver
        elif ext == "bson":
            engine = EngineEnum.mongodb
        else:
            return False, [f"Extensión no permitida: {ext}"]
            
        logs = [f"Iniciando verificación para archivo {file_name} con extensión {ext}"]
        
        if ext == "sql":
            # Try both mysql and postgres verify strategy
            mysql_strategy = get_engine_strategy(EngineEnum.mysql)
            pg_strategy = get_engine_strategy(EngineEnum.postgresql)
            
            mysql_ok, m_logs = await mysql_strategy.verify(file_path)
            if mysql_ok:
                logs.extend(m_logs)
                return True, logs
                
            pg_ok, p_logs = await pg_strategy.verify(file_path)
            if pg_ok:
                logs.extend(p_logs)
                return True, logs
                
            logs.extend(["No se encontró firma válida ni para MySQL ni para PostgreSQL."])
            return False, logs
        else:
            strategy = get_engine_strategy(engine)
            success, s_logs = await strategy.verify(file_path)
            logs.extend(s_logs)
            return success, logs
