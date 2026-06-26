"""
Estados FSM (Máquina de Estados Finita) para los flujos conversacionales del bot.
"""
from aiogram.fsm.state import State, StatesGroup


class GenerarBackupStates(StatesGroup):
    """Estados para el flujo de generación de backup."""
    esperando_motor = State()
    esperando_host = State()
    esperando_puerto = State()
    esperando_usuario = State()
    esperando_contrasena = State()
    esperando_nombre_bd = State()
    confirmacion = State()


class VerificarBackupStates(StatesGroup):
    """Estados para el flujo de verificación de backup."""
    esperando_archivo = State()
