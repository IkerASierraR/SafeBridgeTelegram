from src.services.engines.base import BaseEngine
from src.services.engines.mysql import MySQLEngine
from src.services.engines.postgres import PostgresEngine
from src.services.engines.sqlserver import SQLServerEngine
from src.services.engines.mongodb import MongoDBEngine
from src.models.schemas import EngineEnum

def get_engine_strategy(engine_type: EngineEnum) -> BaseEngine:
    if engine_type == EngineEnum.mysql:
        return MySQLEngine()
    elif engine_type == EngineEnum.postgresql:
        return PostgresEngine()
    elif engine_type == EngineEnum.sqlserver:
        return SQLServerEngine()
    elif engine_type == EngineEnum.mongodb:
        return MongoDBEngine()
    else:
        raise ValueError(f"Motor no soportado: {engine_type}")
