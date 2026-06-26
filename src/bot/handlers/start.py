"""
Handlers para los comandos /start y /ayuda.
"""
from aiogram import Router, types
from aiogram.filters import CommandStart, Command

router = Router()


@router.message(CommandStart())
async def cmd_start(message: types.Message) -> None:
    """Saludo inicial y menú de comandos disponibles."""
    await message.answer(
        f"👋 ¡Hola, {message.from_user.first_name}!\n\n"
        "Soy **SafeBridge Assistant**, tu gestor de backups de bases de datos.\n\n"
        "📋 **Comandos disponibles:**\n\n"
        "🔹 /generar — Generar un backup de tu base de datos\n"
        "🔹 /verificar — Verificar la integridad de un archivo de backup\n"
        "🔹 /ayuda — Ver esta lista de comandos\n"
        "🔹 /cancelar — Cancelar cualquier operación en curso\n\n"
        "Escribe un comando para comenzar. 🚀",
        parse_mode="Markdown",
    )


@router.message(Command("ayuda"))
async def cmd_ayuda(message: types.Message) -> None:
    """Muestra la ayuda detallada del bot."""
    await message.answer(
        "📖 **Guía de SafeBridge**\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🔸 **/generar**\n"
        "Te guiaré paso a paso para conectarme a tu base de datos y generar un backup.\n"
        "Motores soportados: PostgreSQL, MySQL, SQL Server, MongoDB.\n\n"
        "🔸 **/verificar**\n"
        "Súbeme un archivo de backup (.sql, .bak, .bson) y verificaré si está sano o corrupto.\n"
        "Peso máximo: 20 MB.\n\n"
        "🔸 **/cancelar**\n"
        "Cancela cualquier operación que esté en curso.\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "💡 *Tip:* También puedes escribir `cancelar` en cualquier momento para abortar.",
        parse_mode="Markdown",
    )
