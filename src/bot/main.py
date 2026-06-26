import os
import logging
import json
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from aiogram.types import FSInputFile
from dotenv import load_dotenv
import httpx
import tempfile
import asyncio

# Cargar variables de entorno
load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_URL = os.getenv("API_URL", "http://api:8000/api/v1")

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicializar bot y dispatcher
bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def command_start_handler(message: types.Message) -> None:
    """
    Manejador para el comando /start
    """
    await message.answer(
        "¡Hola! Soy el Bot de SafeBridge.\n"
        "Puedo interactuar con la API para generar backups.\n"
        "Usa /backup para ver un ejemplo de generación de backup."
    )

@dp.message(Command("backup"))
async def command_backup_handler(message: types.Message) -> None:
    """
    Ejemplo de comando /backup que invoca a la API interna.
    En una implementación real, podrías pedirle al usuario los datos con una conversación (FSM).
    Por ahora, mandaremos un payload de prueba o requeriremos formato.
    """
    await message.answer("Iniciando solicitud de backup. Por favor espera...")
    
    # Payload de ejemplo, aquí deberías recolectar los datos reales del usuario
    payload = {
        "motor": "postgresql",
        "host": "tu_host",
        "puerto": 5432,
        "usuario": "tu_usuario",
        "contrasena": "tu_password",
        "nombre_bd": "tu_bd"
    }
    
    # En la vida real, podrías usar httpx para hacer un request al endpoint de backup
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:  # 5 minutos de timeout
            response = await client.post(f"{API_URL}/generar", json=payload)
            
            if response.status_code == 200:
                # La API retorna el archivo
                logs_header = response.headers.get("x-backup-logs", "[]")
                status_header = response.headers.get("x-backup-status", "UNKNOWN")
                
                # Decodificar logs
                try:
                    logs = json.loads(logs_header.encode('latin1').decode('unicode_escape'))
                except:
                    logs = [logs_header]
                
                logs_text = "\n".join(logs)
                
                # Guardar archivo temporal para enviarlo
                content_disposition = response.headers.get("content-disposition", "")
                filename = "backup.sql" # Fallback
                if "filename=" in content_disposition:
                    filename = content_disposition.split("filename=")[1].strip('"')
                    
                with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{filename}") as tmp:
                    tmp.write(response.content)
                    tmp_path = tmp.name
                    
                # Enviar mensaje con status
                await message.answer(f"Backup Finalizado.\nEstado: {status_header}\nLogs:\n```\n{logs_text}\n```", parse_mode="Markdown")
                
                # Enviar documento
                document = FSInputFile(tmp_path, filename=filename)
                await message.answer_document(document)
                
                # Limpiar archivo temporal del bot
                os.remove(tmp_path)
            else:
                await message.answer(f"Error al contactar con la API: {response.status_code}\n{response.text}")
    except httpx.ConnectError:
        await message.answer("Error crítico: No pude conectarme a la API. Verifica que el contenedor 'api' esté corriendo.")
    except Exception as e:
        logger.error(f"Error en comando backup: {e}")
        await message.answer(f"Ocurrió un error inesperado: {str(e)}")


async def main() -> None:
    if not TOKEN or TOKEN == "tu_token_aqui_generado_por_botfather":
        logger.error("¡ERROR! TELEGRAM_BOT_TOKEN no configurado en variables de entorno.")
        return
        
    logger.info("Iniciando bot...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
