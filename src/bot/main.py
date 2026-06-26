"""
SafeBridge Telegram Bot — Punto de entrada principal.
Registra todos los routers (handlers) y arranca el polling.
"""
import os
import logging
import asyncio

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    """Inicializa el bot, registra los routers y arranca el polling."""
    if not TOKEN or TOKEN == "tu_token_aqui_generado_por_botfather":
        logger.error("ERROR: TELEGRAM_BOT_TOKEN no está configurado. Revisa tu archivo .env")
        return

    # Inicializar bot y dispatcher con almacenamiento FSM en memoria
    bot = Bot(token=TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Importar y registrar los routers de cada módulo
    from src.bot.handlers.start import router as start_router
    from src.bot.handlers.generar import router as generar_router
    from src.bot.handlers.verificar import router as verificar_router

    dp.include_router(start_router)
    dp.include_router(generar_router)
    dp.include_router(verificar_router)

    logger.info("SafeBridge Bot iniciado correctamente. Escuchando mensajes...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
