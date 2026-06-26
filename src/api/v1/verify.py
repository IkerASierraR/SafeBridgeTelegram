from fastapi import APIRouter, UploadFile, File
from src.models.schemas import VerifyResponse
from src.services.verify_service import VerifyService
from src.core.exceptions import ValidationException
from src.core.config import settings
import os
import aiofiles

router = APIRouter()

ALLOWED_EXTENSIONS = {".sql", ".bak", ".bson"}

@router.post("/verificar", response_model=VerifyResponse)
async def verificar_backup(file: UploadFile = File(...)):
    """
    Verifica un archivo de backup subido.
    Valida la extensión y llama a la lógica de verificación correspondiente.
    """
    _, ext = os.path.splitext(file.filename)
    if ext.lower() not in ALLOWED_EXTENSIONS:
        raise ValidationException(f"Extensión inválida. Permitidas: {', '.join(ALLOWED_EXTENSIONS)}")
        
    temp_path = os.path.join(settings.TEMP_DIR, f"verify_{file.filename}")
    
    try:
        async with aiofiles.open(temp_path, 'wb') as out_file:
            while content := await file.read(1024 * 1024):  # chunk de 1MB
                await out_file.write(content)
                
        success, logs = await VerifyService.verify_uploaded_file(temp_path, file.filename)
        
        status = "Sano" if success else "Corrupto"
        return VerifyResponse(status=status, logs=logs, file_name=file.filename)
    except Exception as e:
        raise ValidationException(f"Error procesando el archivo: {str(e)}")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
