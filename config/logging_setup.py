from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Флаг для предотвращения повторной инициализации
_logging_configured = False


def setup_logging(
    log_file: Path | str,
    *,
    level: int = logging.INFO,
    max_bytes: int = 5 * 1024 * 1024,
    backup_count: int = 5,
) -> None:
    global _logging_configured
    
    # Если логирование уже настроено, пропускаем повторную инициализацию
    if _logging_configured:
        return
    
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(LOG_FORMAT)

    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Правильно закрываем и удаляем все существующие обработчики
    for handler in list(root_logger.handlers):
        handler.close()
        root_logger.removeHandler(handler)

    # Отключаем lastResort handler для предотвращения дублирования
    root_logger.lastResort = None

    # Добавляем обработчики (после очистки они гарантированно отсутствуют)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Помечаем, что логирование настроено
    _logging_configured = True


__all__ = ["setup_logging"]
