from abc import ABC, abstractmethod
from typing import Tuple, List
from src.models.schemas import BackupRequest

class BaseEngine(ABC):
    @abstractmethod
    async def backup(self, request: BackupRequest, file_path: str) -> Tuple[bool, List[str]]:
        """
        Ejecuta el backup y retorna (éxito, logs)
        """
        pass

    @abstractmethod
    async def verify(self, file_path: str, request: BackupRequest = None) -> Tuple[bool, List[str]]:
        """
        Verifica el archivo de backup (intentando restaurar o verificando firma) y retorna (éxito, logs)
        """
        pass
