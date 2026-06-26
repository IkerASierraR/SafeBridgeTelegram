from pydantic import BaseModel, Field, validator
from enum import Enum
from typing import Optional, List

class EngineEnum(str, Enum):
    mongodb = "mongodb"
    sqlserver = "sqlserver"
    mysql = "mysql"
    postgresql = "postgresql"

class BackupRequest(BaseModel):
    motor: EngineEnum
    host: str
    puerto: int
    usuario: str
    contrasena: str
    nombre_bd: str
    
    @validator("puerto")
    def validate_port(cls, v):
        if v < 1 or v > 65535:
            raise ValueError("El puerto debe estar entre 1 y 65535")
        return v

class VerifyResponse(BaseModel):
    status: str = Field(description="Sano o Corrupto")
    logs: List[str]
    file_name: str
