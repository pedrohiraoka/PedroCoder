"""Unit tests for LTA core modules."""

import pytest


class TestConfig:
    """Tests for configuration module."""

    def test_config_import(self) -> None:
        """Test that config module can be imported."""
        from lta.config import Config, ConfigManager, get_config
        assert Config is not None
        assert ConfigManager is not None
        assert get_config is not None

    def test_default_config_creation(self) -> None:
        """Test creating default configuration."""
        from lta.config import Config, NetworkConfig
        
        config = Config()
        assert config.network is not None
        assert isinstance(config.network, NetworkConfig)
        assert len(config.network.ip_backends) > 0

    def test_network_config_defaults(self) -> None:
        """Test network configuration defaults."""
        from lta.config import NetworkConfig
        
        net_config = NetworkConfig()
        assert net_config.timeout_seconds == 10
        assert net_config.max_retries == 3


class TestLogger:
    """Tests for logger module."""

    def test_logger_import(self) -> None:
        """Test that logger module can be imported."""
        from lta.logger import setup_logger, get_log_level_from_string
        assert setup_logger is not None
        assert get_log_level_from_string is not None

    def test_setup_logger(self) -> None:
        """Test logger setup."""
        import logging
        from lta.logger import setup_logger
        
        logger = setup_logger("test_logger")
        assert logger is not None
        assert isinstance(logger, logging.Logger)
        assert logger.level == logging.INFO

    def test_log_level_conversion(self) -> None:
        """Test log level string conversion."""
        import logging
        from lta.logger import get_log_level_from_string
        
        assert get_log_level_from_string("debug") == logging.DEBUG
        assert get_log_level_from_string("info") == logging.INFO
        assert get_log_level_from_string("warning") == logging.WARNING
        assert get_log_level_from_string("error") == logging.ERROR
        assert get_log_level_from_string("critical") == logging.CRITICAL
        assert get_log_level_from_string("unknown") == logging.INFO


class TestShell:
    """Tests for shell utilities."""

    def test_shell_import(self) -> None:
        """Test that shell module can be imported."""
        from lta.utils.shell import (
            run_command,
            which,
            is_root,
            ShellError,
            CommandResult,
        )
        assert run_command is not None
        assert which is not None
        assert is_root is not None

    def test_run_command_success(self) -> None:
        """Test successful command execution."""
        from lta.utils.shell import run_command
        
        result = run_command(["echo", "hello"])
        assert result.success
        assert result.returncode == 0
        assert "hello" in result.stdout

    def test_run_command_failure(self) -> None:
        """Test failed command execution."""
        from lta.utils.shell import run_command
        
        result = run_command(["false"])
        assert not result.success
        assert result.returncode != 0

    def test_which_found(self) -> None:
        """Test finding existing command."""
        from lta.utils.shell import which
        
        path = which("python3") or which("python")
        assert path is not None

    def test_which_not_found(self) -> None:
        """Test finding non-existing command."""
        from lta.utils.shell import which
        
        path = which("nonexistent_command_xyz123")
        assert path is None


class TestSystem:
    """Tests for system utilities."""

    def test_system_import(self) -> None:
        """Test that system module can be imported."""
        from lta.utils.system import (
            get_system_info,
            get_resource_usage,
            get_distro_info,
        )
        assert get_system_info is not None
        assert get_resource_usage is not None
        assert get_distro_info is not None

    def test_get_system_info(self) -> None:
        """Test getting system information."""
        from lta.utils.system import get_system_info
        
        info = get_system_info()
        assert info.hostname is not None
        assert info.os_name is not None
        assert info.cpu_count > 0
        assert info.total_memory_gb > 0

    def test_get_resource_usage(self) -> None:
        """Test getting resource usage."""
        from lta.utils.system import get_resource_usage
        
        usage = get_resource_usage()
        assert 0 <= usage.cpu_percent <= 100
        assert 0 <= usage.memory_percent <= 100
        assert 0 <= usage.disk_percent <= 100

    def test_get_distro_info(self) -> None:
        """Test getting distribution information."""
        from lta.utils.system import get_distro_info
        
        distro = get_distro_info()
        assert "id" in distro
        assert "name" in distro
        assert "version" in distro


class TestNetwork:
    """Tests for network utilities."""

    def test_network_import(self) -> None:
        """Test that network module can be imported."""
        from lta.utils.network import (
            IPResolver,
            dns_lookup,
            ping,
            NetworkError,
        )
        assert IPResolver is not None
        assert dns_lookup is not None
        assert ping is not None

    def test_ip_resolver_creation(self) -> None:
        """Test creating IP resolver."""
        from lta.utils.network import IPResolver
        
        resolver = IPResolver()
        assert resolver is not None
        assert resolver.config is not None

    def test_ping_localhost(self) -> None:
        """Test pinging localhost."""
        from lta.utils.network import ping
        
        stats = ping("127.0.0.1", count=2, timeout=2)
        assert "success" in stats
        assert "packets_sent" in stats


class TestMain:
    """Tests for main CLI module."""

    def test_main_import(self) -> None:
        """Test that main module can be imported."""
        from lta.main import app
        assert app is not None

    def test_version_option(self) -> None:
        """Test version option exists."""
        from lta import __version__
        assert __version__ is not None
        assert isinstance(__version__, str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
