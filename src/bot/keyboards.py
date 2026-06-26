"""
Teclados interactivos (InlineKeyboard y ReplyKeyboard) para el bot.
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove


def motor_keyboard() -> InlineKeyboardMarkup:
    """Teclado con botones para seleccionar el motor de base de datos."""
    buttons = [
        [
            InlineKeyboardButton(text="🐘 PostgreSQL", callback_data="motor_postgresql"),
            InlineKeyboardButton(text="🐬 MySQL", callback_data="motor_mysql"),
        ],
        [
            InlineKeyboardButton(text="🟦 SQL Server", callback_data="motor_sqlserver"),
            InlineKeyboardButton(text="🍃 MongoDB", callback_data="motor_mongodb"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def confirmacion_keyboard() -> InlineKeyboardMarkup:
    """Teclado para confirmar o cancelar la operación."""
    buttons = [
        [
            InlineKeyboardButton(text="✅ Confirmar", callback_data="confirmar_si"),
            InlineKeyboardButton(text="❌ Cancelar", callback_data="confirmar_no"),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def cancelar_keyboard() -> ReplyKeyboardMarkup:
    """Teclado persistente con botón de cancelar."""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Cancelar")]],
        resize_keyboard=True,
        one_time_keyboard=False,
    )


# Constante para remover teclados personalizados
REMOVE_KEYBOARD = ReplyKeyboardRemove()
