"""
Handlers para el flujo de verificación de backup.
El usuario sube un archivo y el bot lo envía a la API para validar su integridad.
"""
import os
import logging
import tempfile

from aiogram import Router, types, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from src.bot.states import VerificarBackupStates
from src.bot.keyboards import cancelar_keyboard, REMOVE_KEYBOARD
from src.bot.services.api_client import solicitar_verificacion

logger = logging.getLogger(__name__)
router = Router()

# Extensiones permitidas y tamaño máximo
EXTENSIONES_VALIDAS = {".sql", ".bak", ".bson"}
MAX_FILE_SIZE_MB = 20
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


# ─────────────────────────────────────────
# Comando /verificar — Inicia el flujo
# ─────────────────────────────────────────
@router.message(Command("verificar"))
async def cmd_verificar(message: types.Message, state: FSMContext) -> None:
    """Inicia el flujo de verificación de backup."""
    await state.clear()

    extensiones = ", ".join(EXTENSIONES_VALIDAS)
    await message.answer(
        "🔍 **Verificar Backup**\n\n"
        f"Envíame el archivo de backup que deseas verificar.\n\n"
        f"📎 Extensiones permitidas: `{extensiones}`\n"
        f"📏 Tamaño máximo: {MAX_FILE_SIZE_MB} MB\n\n"
        "_Arrastra el archivo al chat o usa el clip 📎 para adjuntarlo._",
        parse_mode="Markdown",
        reply_markup=cancelar_keyboard(),
    )
    await state.set_state(VerificarBackupStates.esperando_archivo)


# ─────────────────────────────────────────
# Recibir el archivo subido
# ─────────────────────────────────────────
@router.message(VerificarBackupStates.esperando_archivo, F.document)
async def recibir_archivo(message: types.Message, state: FSMContext, bot: Bot) -> None:
    """Recibe el archivo, lo valida y lo envía a la API."""
    documento = message.document
    filename = documento.file_name or "archivo_desconocido"

    # Validar extensión
    _, ext = os.path.splitext(filename)
    if ext.lower() not in EXTENSIONES_VALIDAS:
        extensiones = ", ".join(EXTENSIONES_VALIDAS)
        await message.answer(
            f"❌ **Extensión no permitida:** `{ext}`\n\n"
            f"Solo acepto archivos con extensión: `{extensiones}`\n"
            "Intenta de nuevo o escribe /cancelar.",
            parse_mode="Markdown",
        )
        return

    # Validar tamaño
    if documento.file_size and documento.file_size > MAX_FILE_SIZE_BYTES:
        size_mb = documento.file_size / (1024 * 1024)
        await message.answer(
            f"❌ **Archivo demasiado grande:** {size_mb:.1f} MB\n\n"
            f"El tamaño máximo permitido es {MAX_FILE_SIZE_MB} MB.\n"
            "Intenta con un archivo más pequeño o escribe /cancelar.",
            parse_mode="Markdown",
        )
        return

    # Descargar archivo
    aviso = await message.answer("⏳ Descargando y verificando archivo... Esto puede tardar.")

    tmp_path = None
    try:
        # Descargar el archivo de Telegram a un temporal
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{filename}") as tmp:
            tmp_path = tmp.name

        await bot.download(documento, destination=tmp_path)

        # Enviar a la API para verificación
        exito, status, logs = await solicitar_verificacion(tmp_path, filename)

        if exito:
            # Determinar emoji según estado
            if status.lower() == "sano":
                emoji = "✅"
                estado_texto = "SANO"
            else:
                emoji = "⛔"
                estado_texto = "CORRUPTO"

            logs_texto = "\n".join(logs) if logs else "Sin logs adicionales."

            await message.answer(
                f"{emoji} **Resultado de Verificación**\n\n"
                f"📄 Archivo: `{filename}`\n"
                f"🔎 Estado: **{estado_texto}**\n\n"
                f"📝 **Logs:**\n```\n{logs_texto}\n```",
                parse_mode="Markdown",
                reply_markup=REMOVE_KEYBOARD,
            )
        else:
            await message.answer(
                f"{status}",
                reply_markup=REMOVE_KEYBOARD,
            )

    except Exception as e:
        logger.error(f"Error procesando archivo: {e}")
        await message.answer(
            f"💥 Error procesando el archivo: {str(e)}",
            reply_markup=REMOVE_KEYBOARD,
        )
    finally:
        # Limpiar archivo temporal
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass

        # Borrar el mensaje de "descargando..."
        try:
            await aviso.delete()
        except Exception:
            pass

    await state.clear()


# ─────────────────────────────────────────
# Si manda texto en vez de archivo
# ─────────────────────────────────────────
@router.message(VerificarBackupStates.esperando_archivo)
async def archivo_no_recibido(message: types.Message, state: FSMContext) -> None:
    """Si el usuario manda texto en vez de un archivo."""
    texto = message.text.strip() if message.text else ""

    if texto == "❌ Cancelar" or texto.lower() == "/cancelar":
        await state.clear()
        await message.answer("🚫 Operación cancelada.", reply_markup=REMOVE_KEYBOARD)
        return

    await message.answer(
        "⚠️ Necesito un **archivo**, no texto.\n\n"
        "Usa el clip 📎 para adjuntar tu archivo de backup, o escribe /cancelar para salir.",
        parse_mode="Markdown",
    )
