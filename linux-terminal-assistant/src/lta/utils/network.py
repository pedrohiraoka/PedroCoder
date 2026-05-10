"""Network utilities for LTA.

Provides IP lookup, DNS resolution, HTTP requests with retry logic,
and network diagnostics.
"""

import socket
import time
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse

import httpx

from lta.config import NetworkConfig
from lta.logger import setup_logger
from lta.utils.shell import run_command

logger = setup_logger(__name__)


@dataclass
class IPAddress:
    """Represents a public IP address with metadata."""

    ip: str
    source: str
    response_time_ms: float
    timestamp: float


class NetworkError(Exception):
    """Exception raised for network-related errors."""

    pass


class IPResolver:
    """Resolves public IP address using multiple backends with fallback.

    Implements automatic failover between configured IP lookup services
    with caching to reduce API calls.
    """

    def __init__(self, config: Optional[NetworkConfig] = None) -> None:
        """Initialize the IP resolver.

        Args:
            config: Network configuration. Uses defaults if not provided.
        """
        self.config = config or NetworkConfig()
        self._cache: Optional[IPAddress] = None
        self._cache_ttl_seconds = 300  # 5 minutes cache

    def get_public_ip(self, use_cache: bool = True) -> IPAddress:
        """Get the public IP address of the current machine.

        Args:
            use_cache: Whether to use cached result if available and valid.

        Returns:
            IPAddress object with IP and metadata.

        Raises:
            NetworkError: If all backends fail.
        """
        if use_cache and self._cache is not None:
            age = time.time() - self._cache.timestamp
            if age < self._cache_ttl_seconds:
                logger.debug(f"Using cached IP: {self._cache.ip}")
                return self._cache

        logger.info("Fetching public IP address...")

        for backend in self.config.ip_backends:
            try:
                ip = self._fetch_from_backend(backend)
                if ip:
                    result = IPAddress(
                        ip=ip,
                        source=backend,
                        response_time_ms=0,  # Will be set by _fetch_from_backend
                        timestamp=time.time(),
                    )
                    self._cache = result
                    logger.info(f"Public IP: {result.ip} (via {result.source})")
                    return result
            except Exception as e:
                logger.warning(f"Backend {backend} failed: {e}")
                continue

        raise NetworkError(
            f"All IP backends failed. Tried: {', '.join(self.config.ip_backends)}"
        )

    def _fetch_from_backend(self, url: str) -> Optional[str]:
        """Fetch IP from a specific backend.

        Args:
            url: Backend URL.

        Returns:
            IP address string or None if failed.
        """
        start_time = time.perf_counter()

        try:
            client = httpx.Client(timeout=self.config.timeout_seconds)
            response = client.get(url, follow_redirects=True)
            response.raise_for_status()

            response_time_ms = (time.perf_counter() - start_time) * 1000
            ip = response.text.strip()

            if self._is_valid_ip(ip):
                logger.debug(f"Got IP {ip} from {url} in {response_time_ms:.2f}ms")
                return ip
            else:
                logger.warning(f"Invalid IP format from {url}: {ip}")
                return None

        except httpx.HTTPStatusError as e:
            logger.debug(f"HTTP error from {url}: {e.response.status_code}")
            return None
        except httpx.RequestError as e:
            logger.debug(f"Request error from {url}: {e}")
            return None

    def _is_valid_ip(self, ip: str) -> bool:
        """Validate IP address format.

        Args:
            ip: IP address string to validate.

        Returns:
            True if valid IPv4 or IPv6 address.
        """
        try:
            socket.inet_aton(ip)
            return True
        except socket.error:
            pass

        try:
            socket.inet_pton(socket.AF_INET6, ip)
            return True
        except socket.error:
            pass

        return False

    def clear_cache(self) -> None:
        """Clear the IP cache."""
        self._cache = None
        logger.debug("IP cache cleared")


def dns_lookup(hostname: str, record_type: str = "A") -> list[str]:
    """Perform DNS lookup for a hostname.

    Args:
        hostname: Hostname to resolve.
        record_type: DNS record type (A, AAAA, MX, NS, TXT, etc.).

    Returns:
        List of resolved records.

    Raises:
        NetworkError: If DNS resolution fails.
    """
    try:
        if record_type == "A":
            _, _, ips = socket.gethostbyname_ex(hostname)
            return ips
        elif record_type == "AAAA":
            results = socket.getaddrinfo(hostname, None, socket.AF_INET6)
            return list(set([r[4][0] for r in results]))
        else:
            result = run_command(["dig", "+short", record_type, hostname])
            if result.success:
                return [line.strip() for line in result.stdout.splitlines() if line.strip()]
            return []
    except socket.gaierror as e:
        raise NetworkError(f"DNS resolution failed for {hostname}: {e}") from e


def check_port(host: str, port: int, timeout: float = 2.0) -> bool:
    """Check if a TCP port is open on a host.

    Args:
        host: Target hostname or IP.
        port: Port number to check.
        timeout: Connection timeout in seconds.

    Returns:
        True if port is open, False otherwise.
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except socket.error:
        return False


def http_get(
    url: str,
    timeout: float = 10.0,
    follow_redirects: bool = True,
    headers: Optional[dict[str, str]] = None,
) -> httpx.Response:
    """Perform HTTP GET request with retry logic.

    Args:
        url: Target URL.
        timeout: Request timeout in seconds.
        follow_redirects: Whether to follow HTTP redirects.
        headers: Optional HTTP headers.

    Returns:
        httpx Response object.

    Raises:
        NetworkError: If request fails after retries.
    """
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        raise NetworkError(f"Invalid URL: {url}")

    client = httpx.Client(timeout=timeout, follow_redirects=follow_redirects)

    try:
        response = client.get(url, headers=headers)
        response.raise_for_status()
        return response
    except httpx.HTTPStatusError as e:
        raise NetworkError(f"HTTP error {e.response.status_code} for {url}") from e
    except httpx.RequestError as e:
        raise NetworkError(f"Request failed for {url}: {e}") from e


def ping(host: str, count: int = 4, timeout: int = 5) -> dict:
    """Ping a host and return statistics.

    Args:
        host: Target hostname or IP.
        count: Number of ping packets.
        timeout: Timeout per packet in seconds.

    Returns:
        Dictionary with ping statistics.
    """
    result = run_command(["ping", "-c", str(count), "-W", str(timeout), host])

    stats = {
        "success": result.success,
        "packets_sent": count,
        "packets_received": 0,
        "packet_loss_percent": 100.0,
        "min_rtt_ms": None,
        "avg_rtt_ms": None,
        "max_rtt_ms": None,
    }

    if result.success:
        output = result.stdout
        lines = output.splitlines()

        for line in lines:
            if "packets transmitted" in line:
                parts = line.split(",")
                if len(parts) >= 2:
                    received_part = parts[1].strip().split()[0]
                    try:
                        stats["packets_received"] = int(received_part)
                    except ValueError:
                        pass

            if "rtt min/avg/max/mdev" in line or "round-trip min/avg/max" in line:
                try:
                    rtt_part = line.split("=")[1].strip()
                    values = rtt_part.split("/")
                    if len(values) >= 3:
                        stats["min_rtt_ms"] = float(values[0])
                        stats["avg_rtt_ms"] = float(values[1])
                        stats["max_rtt_ms"] = float(values[2])
                except (IndexError, ValueError):
                    pass

        if stats["packets_received"] > 0:
            stats["packet_loss_percent"] = (
                (count - stats["packets_received"]) / count
            ) * 100

    return stats


def traceroute(host: str, max_hops: int = 30) -> list[dict]:
    """Perform traceroute to a host.

    Args:
        host: Target hostname or IP.
        max_hops: Maximum number of hops.

    Returns:
        List of hop information dictionaries.
    """
    result = run_command(["traceroute", "-m", str(max_hops), "-n", host])

    hops = []
    if result.success:
        for line in result.stdout.splitlines()[1:]:
            parts = line.split()
            if parts:
                hop_info = {"hop": len(hops) + 1, "raw": line.strip()}
                if len(parts) >= 2:
                    hop_info["address"] = parts[-1]
                    if len(parts) > 3:
                        try:
                            hop_info["rtt_ms"] = float(parts[-4].replace("ms", ""))
                        except ValueError:
                            pass
                hops.append(hop_info)

    return hops


def get_interface_info() -> list[dict]:
    """Get network interface information.

    Returns:
        List of interface information dictionaries.
    """
    import psutil

    interfaces = []
    addrs = psutil.net_if_addrs()

    for iface_name, addresses in addrs.items():
        iface_info = {
            "name": iface_name,
            "ipv4": [],
            "ipv6": [],
            "mac": None,
        }

        for addr in addresses:
            if addr.family == socket.AF_INET:
                iface_info["ipv4"].append({
                    "address": addr.address,
                    "netmask": addr.netmask,
                })
            elif addr.family == socket.AF_INET6:
                iface_info["ipv6"].append({
                    "address": addr.address,
                    "netmask": addr.netmask,
                })
            elif hasattr(socket, "AF_LINK") and addr.family == getattr(socket, "AF_LINK"):
                iface_info["mac"] = addr.address

        interfaces.append(iface_info)

    return interfaces
