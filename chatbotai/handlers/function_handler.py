"""
Function handlers for ChatBotAI.

Provides capabilities for registering and executing custom Python functions
as well as invoking external APIs with validation and sandboxing.
"""

import inspect
import logging
import re
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Type

logger = logging.getLogger(__name__)


class FunctionHandler:
    """
    Manages registration and execution of custom functions.

    This class provides a safe way to register Python functions that
    can be called by the chatbot during conversations.
    """

    def __init__(self, sandbox_enabled: bool = False) -> None:
        """
        Initialize the function handler.

        Args:
            sandbox_enabled: Enable sandboxing for function execution.
        """
        self._functions: Dict[str, Callable[..., Any]] = {}
        self._schemas: Dict[str, Dict[str, Any]] = {}
        self._sandbox_enabled = sandbox_enabled
        logger.debug("Initialized FunctionHandler (sandbox=%s)",
                     sandbox_enabled)

    def register(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        param_schema: Optional[Dict[str, Any]] = None,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """
        Decorator to register a function.

        Args:
            name: Optional custom name for the function.
            description: Optional description of what the function does.
            param_schema: Optional parameter validation schema.

        Returns:
            The decorator function.
        """
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            func_name = name or func.__name__
            self._functions[func_name] = func

            # Extract schema from function signature if not provided
            schema = param_schema
            if schema is None:
                schema = self._extract_schema(func)

            self._schemas[func_name] = {
                "name": func_name,
                "description": description or func.__doc__ or "",
                "parameters": schema,
            }

            logger.info("Registered function: %s", func_name)
            return func

        return decorator

    def _extract_schema(self, func: Callable[..., Any]) -> Dict[str, Any]:
        """
        Extract parameter schema from function signature.

        Args:
            func: The function to analyze.

        Returns:
            Dictionary describing the function parameters.
        """
        sig = inspect.signature(func)
        properties = {}
        required = []

        for param_name, param in sig.parameters.items():
            param_type = param.annotation
            if param_type == inspect.Parameter.empty:
                param_type = str

            type_map = {
                str: "string",
                int: "integer",
                float: "number",
                bool: "boolean",
                list: "array",
                dict: "object",
            }

            properties[param_name] = {
                "type": type_map.get(param_type, "string"),
                "description": f"Parameter {param_name}",
            }

            if param.default == inspect.Parameter.empty:
                required.append(param_name)

        return {
            "type": "object",
            "properties": properties,
            "required": required,
        }

    def execute(
        self,
        name: str,
        arguments: Optional[Dict[str, Any]] = None,
        validate: bool = True,
    ) -> Any:
        """
        Execute a registered function.

        Args:
            name: Name of the function to execute.
            arguments: Arguments to pass to the function.
            validate: Whether to validate arguments.

        Returns:
            The result of the function execution.

        Raises:
            KeyError: If function is not registered.
            ValueError: If validation fails.
        """
        if name not in self._functions:
            raise KeyError(f"Function '{name}' not registered")

        func = self._functions[name]
        args = arguments or {}

        if validate:
            self._validate_arguments(name, args)

        logger.debug("Executing function '%s' with args: %s", name, args)

        try:
            if self._sandbox_enabled:
                result = self._execute_sandboxed(func, args)
            else:
                result = func(**args)

            logger.debug("Function '%s' returned: %s", name, result)
            return result

        except Exception as e:
            logger.error("Function '%s' execution failed: %s", name, str(e))
            raise

    def _validate_arguments(
        self, name: str, arguments: Dict[str, Any]
    ) -> None:
        """
        Validate function arguments against schema.

        Args:
            name: Name of the function.
            arguments: Arguments to validate.

        Raises:
            ValueError: If validation fails.
        """
        schema = self._schemas.get(name, {})
        params_schema = schema.get("parameters", {})
        required = params_schema.get("required", [])
        properties = params_schema.get("properties", {})

        # Check required parameters
        for req_param in required:
            if req_param not in arguments:
                raise ValueError(f"Missing required parameter: {req_param}")

        # Check parameter types
        for param_name, param_value in arguments.items():
            if param_name in properties:
                expected_type = properties[param_name].get("type", "string")
                if not self._check_type(param_value, expected_type):
                    raise ValueError(
                        f"Invalid type for parameter '{param_name}': "
                        f"expected {expected_type}"
                    )

    def _check_type(self, value: Any, expected_type: str) -> bool:
        """
        Check if a value matches the expected type.

        Args:
            value: The value to check.
            expected_type: The expected type name.

        Returns:
            True if type matches, False otherwise.
        """
        type_map = {
            "string": str,
            "integer": int,
            "number": (int, float),
            "boolean": bool,
            "array": list,
            "object": dict,
        }

        expected = type_map.get(expected_type, str)
        return isinstance(value, expected)

    def _execute_sandboxed(
        self, func: Callable[..., Any], args: Dict[str, Any]
    ) -> Any:
        """
        Execute a function in a sandboxed environment.

        Args:
            func: The function to execute.
            args: Arguments to pass.

        Returns:
            The function result.
        """
        # Basic sandboxing - restrict builtins and globals
        safe_globals = {"__builtins__": {}}
        safe_locals = dict(args)

        # Get function source and execute in restricted environment
        source = inspect.getsource(func)
        exec(source, safe_globals, safe_locals)

        # Call the function from safe_locals
        func_name = func.__name__
        return safe_locals[func_name](**args)

    def get_function_list(self) -> List[Dict[str, Any]]:
        """
        Get list of all registered functions with their schemas.

        Returns:
            List of function schemas.
        """
        return list(self._schemas.values())

    def get_function(self, name: str) -> Optional[Callable[..., Any]]:
        """
        Get a registered function by name.

        Args:
            name: The function name.

        Returns:
            The function or None if not found.
        """
        return self._functions.get(name)

    def unregister(self, name: str) -> bool:
        """
        Unregister a function.

        Args:
            name: The function name.

        Returns:
            True if unregistered, False if not found.
        """
        if name in self._functions:
            del self._functions[name]
            if name in self._schemas:
                del self._schemas[name]
            logger.info("Unregistered function: %s", name)
            return True
        return False


class APIIntegration:
    """
    Handles REST API integrations with validation.

    Provides a clean interface for calling external APIs with
    automatic parameter validation and error handling.
    """

    def __init__(
        self,
        base_url: str,
        headers: Optional[Dict[str, str]] = None,
        timeout: int = 30,
    ) -> None:
        """
        Initialize the API integration.

        Args:
            base_url: Base URL of the API.
            headers: Default headers for all requests.
            timeout: Request timeout in seconds.
        """
        self.base_url = base_url.rstrip("/")
        self.headers = headers or {}
        self.timeout = timeout
        self._endpoints: Dict[str, Dict[str, Any]] = {}
        logger.debug("Initialized APIIntegration for %s", base_url)

    def register_endpoint(
        self,
        name: str,
        method: str = "GET",
        path: str = "",
        param_validator: Optional[Callable[[Dict[str, Any]], bool]] = None,
    ) -> None:
        """
        Register an API endpoint.

        Args:
            name: Name for the endpoint.
            method: HTTP method (GET, POST, PUT, DELETE).
            path: Endpoint path relative to base_url.
            param_validator: Optional function to validate parameters.
        """
        self._endpoints[name] = {
            "method": method.upper(),
            "path": path,
            "param_validator": param_validator,
        }
        logger.info("Registered API endpoint: %s %s", method.upper(), path)

    def call(
        self,
        endpoint_name: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        Call a registered API endpoint.

        Args:
            endpoint_name: Name of the endpoint to call.
            params: Query parameters.
            data: Request body data.

        Returns:
            The API response.

        Raises:
            KeyError: If endpoint is not registered.
            ValueError: If validation fails.
        """
        if endpoint_name not in self._endpoints:
            raise KeyError(f"Endpoint '{endpoint_name}' not registered")

        endpoint = self._endpoints[endpoint_name]

        # Validate parameters
        if endpoint["param_validator"]:
            all_params = {**(params or {}), **(data or {})}
            if not endpoint["param_validator"](all_params):
                raise ValueError("Parameter validation failed")

        # Build request
        url = f"{self.base_url}{endpoint['path']}"
        method = endpoint["method"]

        try:
            import requests

            response = requests.request(
                method=method,
                url=url,
                params=params,
                json=data if method in ["POST", "PUT", "PATCH"] else None,
                headers=self.headers,
                timeout=self.timeout,
            )

            response.raise_for_status()
            return response.json()

        except ImportError:
            logger.error("requests package not installed")
            raise ImportError(
                "Install requests: pip install requests"
            ) from None
        except Exception as e:
            logger.error("API call failed: %s", str(e))
            raise

    def get_endpoints(self) -> List[str]:
        """
        Get list of registered endpoint names.

        Returns:
            List of endpoint names.
        """
        return list(self._endpoints.keys())
