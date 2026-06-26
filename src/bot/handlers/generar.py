"""
Handlers para el flujo de generación de backup usando FSM (Máquina de Estados).
Recolecta datos paso a paso y los envía a la API.
"""
import os
import logging

from aiogram import Router, types, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile

from src.bot.states import GenerarBackupStates
from src.bot.keyboards import motor_keyboard, confirmacion_keyboard, cancelar_keyboard, REMOVE_KEYBOARD
from src.bot.services.api_client import solicitar_backup

logger = logging.getLogger(__name__)
router = Router()

# Puertos por defecto según el motor
PUERTOS_DEFAULT = {
    "postgresql": 5432,
    "mysql": 3306,
    "sqlserver": 1433,
    "mongodb": 27017,
}

MOTOR_NOMBRES = {
    "postgresql": "🐘 PostgreSQL",
    "mysql": "🐬 MySQL",
    "sqlserver": "🟦 SQL Server",
    "mongodb": "🍃 MongoDB",
}


# ─────────────────────────────────────────
# Comando /generar — Inicia el flujo FSM
# ─────────────────────────────────────────
@router.message(Command("generar"))
async def cmd_generar(message: types.Message, state: FSMContext) -> None:
    """Inicia el flujo de generación de backup."""
    await state.clear()
    await message.answer(
        "🗄️ **Generar Backup**\n\n"
        "Vamos a generar un backup paso a paso.\n"
        "Selecciona el motor de base de datos:",
        parse_mode="Markdown",
        reply_markup=motor_keyboard(),
    )
    await state.set_state(GenerarBackupStates.esperando_motor)


# ─────────────────────────────────────────
# Paso 1: Motor (botones inline)
# ─────────────────────────────────────────
@router.callback_query(GenerarBackupStates.esperando_motor, F.data.startswith("motor_"))
async def recibir_motor(callback: CallbackQuery, state: FSMContext) -> None:
    """Recibe la selección del motor de base de datos."""
    motor = callback.data.replace("motor_", "")
    await state.update_data(motor=motor)

    nombre_motor = MOTOR_NOMBRES.get(motor, motor)
    puerto_default = PUERTOS_DEFAULT.get(motor, 5432)

    await callback.message.edit_text(f"✅ Motor seleccionado: **{nombre_motor}**", parse_mode="Markdown")
    await callback.message.answer(
        f"📡 Ahora escribe la **dirección del servidor** (host).\n\n"
        f"_Ejemplo: 192.168.1.100 o mi-servidor.com_",
        parse_mode="Markdown",
        reply_markup=cancelar_keyboard(),
    )
    await state.update_data(puerto_default=puerto_default)
    await state.set_state(GenerarBackupStates.esperando_host)
    await callback.answer()


# ─────────────────────────────────────────
# Paso 2: Host
# ─────────────────────────────────────────
@router.message(GenerarBackupStates.esperando_host)
async def recibir_host(message: types.Message, state: FSMContext) -> None:
    """Recibe el host del servidor."""
    texto = message.text.strip()

    if texto == "❌ Cancelar":
        await _cancelar_flujo(message, state)
        return

    if not texto or " " in texto:
        await message.answer("⚠️ El host no puede contener espacios. Inténtalo de nuevo.")
        return

    await state.update_data(host=texto)
    data = await state.get_data()
    puerto_default = data.get("puerto_default", 5432)

    await message.answer(
        f"🔌 Escribe el **puerto** del servidor.\n\n"
        f"_Presiona enviar sin escribir nada para usar el puerto por defecto: {puerto_default}_",
        parse_mode="Markdown",
    )
    await state.set_state(GenerarBackupStates.esperando_puerto)


# ─────────────────────────────────────────
# Paso 3: Puerto
# ─────────────────────────────────────────
@router.message(GenerarBackupStates.esperando_puerto)
async def recibir_puerto(message: types.Message, state: FSMContext) -> None:
    """Recibe el puerto del servidor."""
    texto = message.text.strip()

    if texto == "❌ Cancelar":
        await _cancelar_flujo(message, state)
        return

    data = await state.get_data()
    puerto_default = data.get("puerto_default", 5432)

    if not texto:
        puerto = puerto_default
    else:
        try:
            puerto = int(texto)
            if puerto < 1 or puerto > 65535:
                raise ValueError()
        except ValueError:
            await message.answer("⚠️ El puerto debe ser un número entre 1 y 65535. Inténtalo de nuevo.")
            return

    await state.update_data(puerto=puerto)
    await message.answer(
        "👤 Escribe el **nombre de usuario** para conectarse a la base de datos.",
        parse_mode="Markdown",
    )
    await state.set_state(GenerarBackupStates.esperando_usuario)


# ─────────────────────────────────────────
# Paso 4: Usuario
# ─────────────────────────────────────────
@router.message(GenerarBackupStates.esperando_usuario)
async def recibir_usuario(message: types.Message, state: FSMContext) -> None:
    """Recibe el nombre de usuario."""
    texto = message.text.strip()

    if texto == "❌ Cancelar":
        await _cancelar_flujo(message, state)
        return

    if not texto:
        await message.answer("⚠️ El usuario no puede estar vacío.")
        return

    await state.update_data(usuario=texto)
    await message.answer(
        "🔑 Escribe la **contraseña** del usuario.\n\n"
        "_No te preocupes, el mensaje será eliminado automáticamente por seguridad._",
        parse_mode="Markdown",
    )
    await state.set_state(GenerarBackupStates.esperando_contrasena)


# ─────────────────────────────────────────
# Paso 5: Contraseña
# ─────────────────────────────────────────
@router.message(GenerarBackupStates.esperando_contrasena)
async def recibir_contrasena(message: types.Message, state: FSMContext, bot: Bot) -> None:
    """Recibe la contraseña y la elimina del chat por seguridad."""
    texto = message.text.strip()

    if texto == "❌ Cancelar":
        await _cancelar_flujo(message, state)
        return

    if not texto:
        await message.answer("⚠️ La contraseña no puede estar vacía.")
        return

    # Intentar eliminar el mensaje con la contraseña por seguridad
    try:
        await message.delete()
    except Exception:
        pass  # Si el bot no tiene permisos para borrar, continúa

    await state.update_data(contrasena=texto)
    await message.answer(
        "🗃️ Escribe el **nombre de la base de datos** que deseas respaldar.",
        parse_mode="Markdown",
    )
    await state.set_state(GenerarBackupStates.esperando_nombre_bd)


# ─────────────────────────────────────────
# Paso 6: Nombre de la base de datos
# ─────────────────────────────────────────
@router.message(GenerarBackupStates.esperando_nombre_bd)
async def recibir_nombre_bd(message: types.Message, state: FSMContext) -> None:
    """Recibe el nombre de la BD y muestra el resumen para confirmar."""
    texto = message.text.strip()

    if texto == "❌ Cancelar":
        await _cancelar_flujo(message, state)
        return

    if not texto:
        await message.answer("⚠️ El nombre de la base de datos no puede estar vacío.")
        return

    await state.update_data(nombre_bd=texto)
    data = await state.get_data()

    motor_nombre = MOTOR_NOMBRES.get(data["motor"], data["motor"])

    resumen = (
        "📋 **Resumen de la operación**\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"🔹 Motor: {motor_nombre}\n"
        f"🔹 Host: `{data['host']}`\n"
        f"🔹 Puerto: `{data['puerto']}`\n"
        f"🔹 Usuario: `{data['usuario']}`\n"
        f"🔹 Contraseña: `{'•' * len(data['contrasena'])}`\n"
        f"🔹 Base de datos: `{data['nombre_bd']}`\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "¿Los datos son correctos?"
    )

    await message.answer(resumen, parse_mode="Markdown", reply_markup=confirmacion_keyboard())
    await state.set_state(GenerarBackupStates.confirmacion)


# ─────────────────────────────────────────
# Paso 7: Confirmación
# ─────────────────────────────────────────
@router.callback_query(GenerarBackupStates.confirmacion, F.data == "confirmar_si")
async def confirmar_backup(callback: CallbackQuery, state: FSMContext) -> None:
    """El usuario confirmó: enviar la solicitud a la API."""
    data = await state.get_data()

    await callback.message.edit_text("⏳ **Generando backup...** Esto puede tardar unos minutos.", parse_mode="Markdown")

    payload = {
        "motor": data["motor"],
        "host": data["host"],
        "puerto": data["puerto"],
        "usuario": data["usuario"],
        "contrasena": data["contrasena"],
        "nombre_bd": data["nombre_bd"],
    }

    exito, mensaje, tmp_path, filename = await solicitar_backup(payload)

    if exito and tmp_path:
        await callback.message.answer(
            f"✅ **{mensaje}**\n\n📦 Aquí tienes tu archivo:",
            parse_mode="Markdown",
            reply_markup=REMOVE_KEYBOARD,
        )
        document = FSInputFile(tmp_path, filename=filename)
        await callback.message.answer_document(document)

        # Limpiar archivo temporal
        try:
            os.remove(tmp_path)
        except Exception:
            pass
    else:
        await callback.message.answer(
            f"{mensaje}",
            reply_markup=REMOVE_KEYBOARD,
        )

    await state.clear()
    await callback.answer()


@router.callback_query(GenerarBackupStates.confirmacion, F.data == "confirmar_no")
async def cancelar_confirmacion(callback: CallbackQuery, state: FSMContext) -> None:
    """El usuario canceló desde la confirmación."""
    await callback.message.edit_text("🚫 Operación cancelada.")
    await state.clear()
    await callback.answer()


# ─────────────────────────────────────────
# Comando /cancelar — Global
# ─────────────────────────────────────────
@router.message(Command("cancelar"))
async def cmd_cancelar(message: types.Message, state: FSMContext) -> None:
    """Cancela cualquier operación en curso."""
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("ℹ️ No hay ninguna operación en curso.", reply_markup=REMOVE_KEYBOARD)
        return

    await state.clear()
    await message.answer("🚫 Operación cancelada.", reply_markup=REMOVE_KEYBOARD)


# ─────────────────────────────────────────
# Helper interno
# ─────────────────────────────────────────
async def _cancelar_flujo(message: types.Message, state: FSMContext) -> None:
    """Cancela el flujo actual cuando el usuario presiona el botón Cancelar."""
    await state.clear()
    await message.answer("🚫 Operación cancelada.", reply_markup=REMOVE_KEYBOARD)
