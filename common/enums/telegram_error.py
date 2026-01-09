from enum import Enum
from typing import Optional


class TelegramErrorType(str, Enum):
    """Типы ошибок Telegram"""
    CHAT_NOT_FOUND = "chat_not_found"
    BOT_KICKED = "bot_kicked"
    BOT_BLOCKED = "bot_blocked"
    FORBIDDEN = "forbidden"
    USER_DEACTIVATED = "user_deactivated"
    NETWORK_ERROR = "network_error"
    SERVER_ERROR = "server_error"
    UNKNOWN = "unknown"


def classify_telegram_error(exception: Exception) -> TelegramErrorType:
    """
    Классифицирует исключение Telegram для определения критичности
    
    Критические ошибки (требуют удаления группы):
    - CHAT_NOT_FOUND: чат удален
    - BOT_KICKED: бот кикнут из группы
    - BOT_BLOCKED: бот заблокирован
    - FORBIDDEN: нет доступа
    - USER_DEACTIVATED: пользователь деактивирован
    
    Некритические ошибки (сетевые/серверные, не останавливают постинг):
    - NETWORK_ERROR: сетевые ошибки (timeout, connection issues)
    - SERVER_ERROR: серверные ошибки (Bad Gateway, 5xx errors)
    
    Args:
        exception: Исключение от aiogram
        
    Returns:
        TelegramErrorType: Тип ошибки
    """
    error_str = str(exception).lower()
    error_type_name = type(exception).__name__
    
    # Проверка сетевых/серверных ошибок по типу исключения
    if error_type_name == "TelegramNetworkError":
        return TelegramErrorType.NETWORK_ERROR
    
    if error_type_name == "TelegramServerError":
        return TelegramErrorType.SERVER_ERROR
    
    # Проверка сетевых/серверных ошибок по тексту
    if any(keyword in error_str for keyword in ["request timeout", "timeout error", "network error", "connection"]):
        return TelegramErrorType.NETWORK_ERROR
    
    if any(keyword in error_str for keyword in ["bad gateway", "server error", "502", "503", "504", "500", "501", "505"]):
        return TelegramErrorType.SERVER_ERROR
    
    # Проверка по типу исключения
    if error_type_name == "ChatNotFound":
        return TelegramErrorType.CHAT_NOT_FOUND
    
    # Проверка по тексту ошибки
    if "chat not found" in error_str:
        return TelegramErrorType.CHAT_NOT_FOUND
    
    if "bot was kicked" in error_str:
        return TelegramErrorType.BOT_KICKED
    
    if "bot was blocked" in error_str or "bot is blocked" in error_str:
        return TelegramErrorType.BOT_BLOCKED
    
    if "user is deactivated" in error_str or "user_deactivated" in error_str:
        return TelegramErrorType.USER_DEACTIVATED
    
    if "forbidden" in error_str and error_type_name == "TelegramForbiddenError":
        return TelegramErrorType.FORBIDDEN
    
    return TelegramErrorType.UNKNOWN


def is_critical_error(error_type: TelegramErrorType) -> bool:
    """
    Проверяет, является ли ошибка критической (требует удаления группы)
    
    Критические ошибки останавливают постинг и удаляют группу.
    Сетевые/серверные ошибки (NETWORK_ERROR, SERVER_ERROR) НЕ являются критическими
    и обрабатываются с повторными попытками.
    
    Args:
        error_type: Тип ошибки
        
    Returns:
        bool: True если ошибка критическая
    """
    return error_type in {
        TelegramErrorType.CHAT_NOT_FOUND,
        TelegramErrorType.BOT_KICKED,
        TelegramErrorType.BOT_BLOCKED,
        TelegramErrorType.FORBIDDEN,
        TelegramErrorType.USER_DEACTIVATED,
    }

