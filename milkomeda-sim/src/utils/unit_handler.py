"""
unit_handler.py - Manipulação segura de unidades físicas com astropy.

Fornece funções utilitárias para conversão, validação e manipulação
de quantidades físicas usando o sistema de unidades do astropy.
"""

from typing import Union, Optional
import numpy as np
from astropy import units as u
from astropy.units import Quantity


class UnitHandler:
    """
    Classe utilitária para manipulação de unidades físicas.

    Attributes:
        default_length: Unidade padrão para comprimento.
        default_velocity: Unidade padrão para velocidade.
        default_mass: Unidade padrão para massa.
        default_time: Unidade padrão para tempo.
    """

    def __init__(
        self,
        default_length: u.Unit = u.kpc,
        default_velocity: u.Unit = u.km / u.s,
        default_mass: u.Unit = u.Msun,
        default_time: u.Unit = u.Gyr,
    ):
        """
        Inicializa o manipulador de unidades.

        Args:
            default_length: Unidade padrão para comprimento.
            default_velocity: Unidade padrão para velocidade.
            default_mass: Unidade padrão para massa.
            default_time: Unidade padrão para tempo.
        """
        self.default_length = default_length
        self.default_velocity = default_velocity
        self.default_mass = default_mass
        self.default_time = default_time

    def convert(
        self,
        value: Union[Quantity, float, int, np.ndarray],
        target_unit: u.Unit,
        default_unit: Optional[u.Unit] = None,
    ) -> Quantity:
        """
        Converte um valor para a unidade alvo.

        Args:
            value: Valor a converter (pode ser Quantity ou numérico).
            target_unit: Unidade de destino.
            default_unit: Unidade padrão se value não for Quantity.

        Returns:
            Quantity: Valor convertido na unidade alvo.

        Raises:
            ValueError: Se a conversão não for possível.
        """
        if isinstance(value, Quantity):
            return value.to(target_unit)
        elif default_unit is not None:
            return (value * default_unit).to(target_unit)
        else:
            raise ValueError(
                f"Valor {value} não tem unidade e nenhum default_unit foi fornecido"
            )

    def to_base_units(self, value: Quantity) -> Quantity:
        """
        Converte uma quantidade para unidades base do SI.

        Args:
            value: Quantidade a converter.

        Returns:
            Quantity: Valor em unidades SI.
        """
        if not isinstance(value, Quantity):
            raise TypeError(f"Esperado Quantity, recebido {type(value)}")
        return value.si

    def get_value_in_unit(self, value: Quantity, unit: u.Unit) -> Union[float, np.ndarray]:
        """
        Extrai o valor numérico de uma Quantity em uma unidade específica.

        Args:
            value: Quantidade física.
            unit: Unidade desejada para o valor numérico.

        Returns:
            float or np.ndarray: Valor numérico na unidade especificada.
        """
        if not isinstance(value, Quantity):
            return value
        return value.to_value(unit)

    def validate_dimension(
        self, value: Quantity, expected_dimension: u.PhysicalType
    ) -> bool:
        """
        Valida se uma quantidade tem a dimensão física esperada.

        Args:
            value: Quantidade a validar.
            expected_dimension: Dimensão física esperada.

        Returns:
            bool: True se a dimensão estiver correta.

        Raises:
            TypeError: Se a dimensão não corresponder.
        """
        if not isinstance(value, Quantity):
            raise TypeError(f"Esperado Quantity, recebido {type(value)}")

        actual_dimension = u.get_physical_type(value.unit)
        if actual_dimension != expected_dimension:
            raise TypeError(
                f"Dimensão inválida: esperado {expected_dimension}, "
                f"recebido {actual_dimension}"
            )
        return True


def convert_units(
    value: Union[Quantity, float, int],
    from_unit: u.Unit,
    to_unit: u.Unit,
) -> Quantity:
    """
    Função utilitária para conversão rápida de unidades.

    Args:
        value: Valor a converter.
        from_unit: Unidade de origem (se value não for Quantity).
        to_unit: Unidade de destino.

    Returns:
        Quantity: Valor convertido.
    """
    if isinstance(value, Quantity):
        return value.to(to_unit)
    return (value * from_unit).to(to_unit)


def safe_quantity(
    value: Union[Quantity, float, int, np.ndarray],
    unit: u.Unit,
) -> Quantity:
    """
    Cria uma Quantity de forma segura, preservando Quantities existentes.

    Args:
        value: Valor (pode já ser Quantity ou numérico).
        unit: Unidade a aplicar se value não for Quantity.

    Returns:
        Quantity: Valor como Quantity.
    """
    if isinstance(value, Quantity):
        return value
    return value * unit


def parse_quantity_string(value_str: str, default_unit: u.Unit) -> Quantity:
    """
    Parseia uma string no formato "valor unidade" ou apenas "valor".

    Args:
        value_str: String a parsear (ex: "765 kpc", "100").
        default_unit: Unidade padrão se nenhuma for especificada.

    Returns:
        Quantity: Valor parseado.

    Examples:
        >>> parse_quantity_string("765 kpc", u.kpc)
        <Quantity 765. kpc>
        >>> parse_quantity_string("100", u.km/u.s)
        <Quantity 100. km / s>
    """
    parts = value_str.strip().split()

    if len(parts) == 1:
        # Apenas valor numérico
        return float(parts[0]) * default_unit
    elif len(parts) == 2:
        # Valor + unidade
        value = float(parts[0])
        unit = u.Unit(parts[1])
        return value * unit
    else:
        raise ValueError(f"Formato inválido: '{value_str}'. Use 'valor [unidade]'")


def format_quantity(value: Quantity, precision: int = 3) -> str:
    """
    Formata uma Quantity para exibição legível.

    Args:
        value: Quantidade a formatar.
        precision: Número de casas decimais.

    Returns:
        str: String formatada (ex: "765.000 kpc").
    """
    if not isinstance(value, Quantity):
        return f"{value:.{precision}f}"

    val = value.value
    unit_str = str(value.unit)

    if isinstance(val, np.ndarray):
        return f"[{val.min():.{precision}f} - {val.max():.{precision}f}] {unit_str}"
    return f"{val:.{precision}f} {unit_str}"
