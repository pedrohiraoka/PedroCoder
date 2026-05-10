"""Safe subprocess wrapper for system command execution.

Provides secure, non-shell command execution with proper
error handling, timeout support, and output capture.
"""

import asyncio
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

from lta.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class CommandResult:
    """Result of a command execution."""

    returncode: int
    stdout: str
    stderr: str
    command: list[str]
    duration_ms: float

    @property
    def success(self) -> bool:
        """Check if command executed successfully."""
        return self.returncode == 0

    def raise_for_status(self) -> None:
        """Raise CalledProcessError if command failed."""
        if not self.success:
            raise subprocess.CalledProcessError(
                self.returncode,
                self.command,
                self.stdout,
                self.stderr,
            )


class ShellError(Exception):
    """Exception raised for shell command execution errors."""

    def __init__(
        self,
        message: str,
        command: Optional[list[str]] = None,
        returncode: Optional[int] = None,
        stdout: Optional[str] = None,
        stderr: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.command = command
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def run_command(
    command: list[str],
    cwd: Optional[Path] = None,
    env: Optional[dict[str, str]] = None,
    timeout: Optional[float] = None,
    capture_output: bool = True,
    check: bool = False,
    sudo: bool = False,
) -> CommandResult:
    """Execute a system command safely without shell=True.

    Args:
        command: Command and arguments as a list (e.g., ['ls', '-la']).
        cwd: Working directory for command execution.
        env: Environment variables (merged with current env).
        timeout: Maximum execution time in seconds.
        capture_output: Whether to capture stdout/stderr.
        check: If True, raise exception on non-zero exit code.
        sudo: If True, prepend 'sudo' to command (requires privileges).

    Returns:
        CommandResult with execution details.

    Raises:
        ShellError: If command execution fails.
        FileNotFoundError: If command binary is not found.
        subprocess.TimeoutExpired: If timeout is exceeded.
    """
    import time

    start_time = time.perf_counter()

    exec_command = command.copy()
    if sudo:
        if shutil.which("sudo") is None:
            raise ShellError("sudo command not found", command=command)
        exec_command = ["sudo"] + exec_command

    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)

    logger.debug(f"Executing command: {' '.join(exec_command)}")

    try:
        result = subprocess.run(
            exec_command,
            cwd=cwd,
            env=merged_env,
            timeout=timeout,
            capture_output=capture_output,
            text=True,
            check=False,
        )

        duration_ms = (time.perf_counter() - start_time) * 1000

        cmd_result = CommandResult(
            returncode=result.returncode,
            stdout=result.stdout or "",
            stderr=result.stderr or "",
            command=exec_command,
            duration_ms=duration_ms,
        )

        if check:
            cmd_result.raise_for_status()

        return cmd_result

    except FileNotFoundError as e:
        raise ShellError(
            f"Command not found: {exec_command[0]}",
            command=exec_command,
        ) from e
    except subprocess.TimeoutExpired as e:
        raise ShellError(
            f"Command timed out after {timeout}s",
            command=exec_command,
            returncode=-1,
        ) from e
    except OSError as e:
        raise ShellError(
            f"OS error during command execution: {e}",
            command=exec_command,
        ) from e


async def run_command_async(
    command: list[str],
    cwd: Optional[Path] = None,
    env: Optional[dict[str, str]] = None,
    timeout: Optional[float] = None,
    sudo: bool = False,
) -> CommandResult:
    """Execute a system command asynchronously.

    Args:
        command: Command and arguments as a list.
        cwd: Working directory for command execution.
        env: Environment variables (merged with current env).
        timeout: Maximum execution time in seconds.
        sudo: If True, prepend 'sudo' to command.

    Returns:
        CommandResult with execution details.

    Raises:
        ShellError: If command execution fails.
    """
    import time

    start_time = time.perf_counter()

    exec_command = command.copy()
    if sudo:
        if shutil.which("sudo") is None:
            raise ShellError("sudo command not found", command=command)
        exec_command = ["sudo"] + exec_command

    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)

    logger.debug(f"Executing async command: {' '.join(exec_command)}")

    try:
        process = await asyncio.create_subprocess_exec(
            *exec_command,
            cwd=cwd,
            env=merged_env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=timeout
            )
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            raise ShellError(
                f"Command timed out after {timeout}s",
                command=exec_command,
                returncode=-1,
            )

        duration_ms = (time.perf_counter() - start_time) * 1000

        return CommandResult(
            returncode=process.returncode or 0,
            stdout=stdout.decode() if stdout else "",
            stderr=stderr.decode() if stderr else "",
            command=exec_command,
            duration_ms=duration_ms,
        )

    except FileNotFoundError as e:
        raise ShellError(
            f"Command not found: {exec_command[0]}",
            command=exec_command,
        ) from e
    except OSError as e:
        raise ShellError(
            f"OS error during command execution: {e}",
            command=exec_command,
        ) from e


def which(command_name: str) -> Optional[str]:
    """Find the full path of a command in PATH.

    Args:
        command_name: Name of the command to find.

    Returns:
        Full path to command or None if not found.
    """
    return shutil.which(command_name)


def require_command(command_name: str) -> str:
    """Ensure a command is available, raising error if not.

    Args:
        command_name: Name of the required command.

    Returns:
        Full path to the command.

    Raises:
        ShellError: If command is not found.
    """
    path = shutil.which(command_name)
    if path is None:
        raise ShellError(
            f"Required command '{command_name}' not found. "
            f"Please install it and ensure it's in your PATH."
        )
    return path


def is_root() -> bool:
    """Check if current process is running as root.

    Returns:
        True if running as root, False otherwise.
    """
    return os.geteuid() == 0


def require_root(operation: str = "this operation") -> None:
    """Ensure the process is running as root.

    Args:
        operation: Description of the operation requiring root.

    Raises:
        ShellError: If not running as root.
    """
    if not is_root():
        raise ShellError(
            f"Root privileges required for {operation}. "
            f"Please run with sudo or as root user."
        )


def get_available_commands(commands: list[str]) -> dict[str, bool]:
    """Check availability of multiple commands.

    Args:
        commands: List of command names to check.

    Returns:
        Dictionary mapping command names to availability status.
    """
    return {cmd: shutil.which(cmd) is not None for cmd in commands}
