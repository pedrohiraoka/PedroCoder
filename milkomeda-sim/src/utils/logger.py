"""
logger.py - Sistema de logging estruturado para Milkomeda.

Fornece logging com níveis INFO, DEBUG, WARNING, ERROR e formatação
consistente em toda a aplicação.
"""

import logging
import sys
from typing import Optional

# Cache de loggers criados
_loggers: dict[str, logging.Logger] = {}


def setup_logger(
    name: str = "milkomeda",
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    console_output: bool = True,
) -> logging.Logger:
    """
    Configura e retorna um logger com formatação personalizada.

    Args:
        name: Nome do logger (geralmente __name__ do módulo).
        level: Nível de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_file: Caminho opcional para arquivo de log.
        console_output: Se True, imprime logs no console.

    Returns:
        logging.Logger: Logger configurado.
    """
    if name in _loggers:
        return _loggers[name]

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False

    # Limpar handlers existentes
    logger.handlers.clear()

    # Formato do log
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Handler de console
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # Handler de arquivo
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    _loggers[name] = logger
    return logger


def get_logger(name: str = "milkomeda") -> logging.Logger:
    """
    Obtém um logger existente ou cria um novo com configuração padrão.

    Args:
        name: Nome do logger.

    Returns:
        logging.Logger: Logger configurado.
    """
    if name in _loggers:
        return _loggers[name]
    return setup_logger(name)


def set_log_level(level: int, name: str = "milkomeda") -> None:
    """
    Altera o nível de logging de um logger existente.

    Args:
        level: Novo nível de logging.
        name: Nome do logger.
    """
    if name in _loggers:
        _loggers[name].setLevel(level)
        for handler in _loggers[name].handlers:
            handler.setLevel(level)
