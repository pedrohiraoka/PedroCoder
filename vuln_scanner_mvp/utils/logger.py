"""
Módulo de logging para a aplicação VulnScanner.
Fornece funções para registrar eventos e resultados de scans.
"""

import logging
import os
from datetime import datetime

# Configuração do logger
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'reports')
os.makedirs(LOG_DIR, exist_ok=True)

def setup_logger(name: str = "vulnscanner") -> logging.Logger:
    """
    Configura e retorna um logger com handlers para arquivo e console.
    
    Args:
        name: Nome do logger
        
    Returns:
        Logger configurado
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Evitar duplicação de handlers
    if logger.handlers:
        return logger
    
    # Formato do log
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler para console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Handler para arquivo
    log_file = os.path.join(LOG_DIR, f"scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger


def get_log_file_path() -> str:
    """
    Retorna o caminho do arquivo de log mais recente.
    
    Returns:
        Caminho do arquivo de log
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return os.path.join(LOG_DIR, f"scan_{timestamp}.log")


logger = setup_logger()
