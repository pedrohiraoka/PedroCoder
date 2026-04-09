"""
Utils - Funções utilitárias e helpers

Funções de normalização, logging, retries e outras utilidades
compartilhadas entre os módulos do crawler.
"""

import logging
import re
import time
import hashlib
from datetime import datetime
from typing import Optional, Callable, Any, List
from urllib.parse import urlparse, urljoin
from pathlib import Path

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import httpx


def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    formato: str = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
) -> logging.Logger:
    """
    Configura logging estruturado para o crawler.
    
    Args:
        level: Nível de logging (DEBUG, INFO, WARNING, ERROR)
        log_file: Caminho para arquivo de log (opcional)
        formato: Formato das mensagens de log
    
    Returns:
        Logger configurado
    """
    logger = logging.getLogger("crawler")
    logger.setLevel(level)
    
    # Limpa handlers existentes
    logger.handlers.clear()
    
    # Handler para console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(logging.Formatter(formato))
    logger.addHandler(console_handler)
    
    # Handler para arquivo (se especificado)
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(logging.Formatter(formato))
        logger.addHandler(file_handler)
    
    return logger


def normalize_phone(phone: str, country: str = "BR") -> Optional[str]:
    """
    Normaliza número de telefone para formato internacional.
    
    Args:
        phone: Número de telefone em qualquer formato
        country: Código do país (ISO 3166-1 alpha-2)
    
    Returns:
        Número normalizado ou None se inválido
    """
    if not phone:
        return None
    
    # Remove todos os caracteres não-dígitos exceto +
    cleaned = re.sub(r'[^\d+]', '', phone.strip())
    
    # Remove zeros iniciais após o +
    if cleaned.startswith('+'):
        cleaned = '+' + cleaned.lstrip('+').lstrip('0')
    else:
        cleaned = cleaned.lstrip('0')
    
    # Adiciona código do país se ausente (Brasil = 55)
    country_codes = {"BR": "55", "US": "1", "PT": "351"}
    code = country_codes.get(country.upper(), "55")
    
    if not cleaned.startswith('+'):
        if not cleaned.startswith(code):
            cleaned = f"+{code}{cleaned}"
        else:
            cleaned = f"+{cleaned}"
    
    # Validação básica: deve ter entre 8 e 15 dígitos (excluindo +)
    digits = re.sub(r'[^\d]', '', cleaned)
    if len(digits) < 8 or len(digits) > 15:
        return None
    
    return cleaned


def normalize_email(email: str) -> Optional[str]:
    """
    Normaliza e valida endereço de e-mail.
    
    Args:
        email: Endereço de e-mail
    
    Returns:
        E-mail normalizado em minúsculas ou None se inválido
    """
    if not email:
        return None
    
    email = email.strip().lower()
    
    # Validação básica de formato
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if re.match(pattern, email):
        return email
    
    return None


def parse_price(price_str: str, currency: str = "BRL") -> Optional[float]:
    """
    Converte string de preço para float.
    
    Args:
        price_str: String com preço (ex: "R$ 1.234,56", "$99.99")
        currency: Moeda esperada
    
    Returns:
        Valor como float ou None se não conseguir parsear
    """
    if not price_str:
        return None
    
    # Remove símbolos de moeda e espaços
    cleaned = re.sub(r'[^\d,.]', '', price_str.strip())
    
    if not cleaned:
        return None
    
    try:
        # Detecta formato (vírgula ou ponto como decimal)
        if ',' in cleaned and '.' in cleaned:
            # Formato europeu/brasileiro: 1.234,56
            cleaned = cleaned.replace('.', '').replace(',', '.')
        elif ',' in cleaned:
            # Pode ser decimal brasileiro ou separador de milhar
            parts = cleaned.split(',')
            if len(parts) == 2 and len(parts[1]) <= 2:
                # Provavelmente decimal
                cleaned = cleaned.replace(',', '.')
            else:
                # Separador de milhar
                cleaned = cleaned.replace(',', '')
        # Se só tem ponto, assume formato americano
        
        value = float(cleaned)
        return value if value >= 0 else None
        
    except (ValueError, TypeError):
        return None


def hash_url(url: str) -> str:
    """
    Gera hash único para URL.
    
    Args:
        url: URL para hashear
    
    Returns:
        Hash MD5 da URL
    """
    return hashlib.md5(url.encode('utf-8')).hexdigest()


def get_domain(url: str) -> str:
    """
    Extrai domínio de uma URL.
    
    Args:
        url: URL completa
    
    Returns:
        Domínio (ex: example.com)
    """
    parsed = urlparse(url)
    return parsed.netloc.lower()


def normalize_url(base_url: str, link: str) -> str:
    """
    Normaliza URL relativa para absoluta.
    
    Args:
        base_url: URL base da página
        link: Link (pode ser relativo ou absoluto)
    
    Returns:
        URL absoluta normalizada
    """
    if not link:
        return base_url
    
    link = link.strip()
    
    # Já é URL absoluta
    if link.startswith(('http://', 'https://')):
        return link
    
    # URL relativa
    return urljoin(base_url, link)


def should_exclude_url(url: str, exclude_patterns: List[str]) -> bool:
    """
    Verifica se URL deve ser excluída baseado em padrões.
    
    Args:
        url: URL para verificar
        exclude_patterns: Lista de padrões regex
    
    Returns:
        True se URL deve ser excluída
    """
    for pattern in exclude_patterns:
        if re.search(pattern, url, re.IGNORECASE):
            return True
    return False


def create_retry_decorator(
    max_attempts: int = 3,
    min_wait: float = 1.0,
    max_wait: float = 60.0
) -> Callable:
    """
    Cria decorator para retry com backoff exponencial.
    
    Args:
        max_attempts: Número máximo de tentativas
        min_wait: Tempo mínimo de espera (segundos)
        max_wait: Tempo máximo de espera (segundos)
    
    Returns:
        Decorator configurado
    """
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(min=min_wait, max=max_wait),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError, httpx.RemoteProtocolError)),
        reraise=True
    )


class RateLimiter:
    """
    Limitador de taxa para respeitar delays entre requisições.
    """
    
    def __init__(self, delay: float = 1.5, requests_per_minute: Optional[int] = None):
        """
        Inicializa limitador de taxa.
        
        Args:
            delay: Delay mínimo entre requisições (segundos)
            requests_per_minute: Limite opcional de requisições por minuto
        """
        self.delay = delay
        self.requests_per_minute = requests_per_minute
        self.last_request_time: float = 0
        self.request_times: List[float] = []
    
    def wait(self) -> None:
        """Espera o tempo necessário antes da próxima requisição."""
        now = time.time()
        
        # Delay básico
        time_since_last = now - self.last_request_time
        if time_since_last < self.delay:
            sleep_time = self.delay - time_since_last
            time.sleep(sleep_time)
        
        # Limite de requests por minuto
        if self.requests_per_minute:
            # Remove timestamps antigos (mais de 1 minuto)
            minute_ago = now - 60
            self.request_times = [t for t in self.request_times if t > minute_ago]
            
            # Verifica se excedeu limite
            if len(self.request_times) >= self.requests_per_minute:
                oldest = min(self.request_times)
                sleep_time = 60 - (now - oldest)
                if sleep_time > 0:
                    time.sleep(sleep_time)
                self.request_times = []  # Reset após espera
        
        self.last_request_time = time.time()
        self.request_times.append(self.last_request_time)


def sanitize_filename(filename: str) -> str:
    """
    Sanitiza nome de arquivo removendo caracteres inválidos.
    
    Args:
        filename: Nome original do arquivo
    
    Returns:
        Nome sanitizado seguro para filesystem
    """
    # Remove caracteres inválidos
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove espaços extras
    sanitized = '_'.join(sanitized.split())
    # Limita tamanho
    return sanitized[:255]


def ensure_dir(path: str) -> Path:
    """
    Garante que diretório existe, criando se necessário.
    
    Args:
        path: Caminho do diretório
    
    Returns:
        Path object do diretório
    """
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def format_duration(seconds: float) -> str:
    """
    Formata duração em segundos para string legível.
    
    Args:
        seconds: Duração em segundos
    
    Returns:
        String formatada (ex: "1h 23m 45s")
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.0f}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours}h {minutes}m {secs:.0f}s"
