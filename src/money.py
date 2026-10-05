"""Operações monetárias compartilhadas pelo motor."""

from decimal import Decimal, ROUND_HALF_UP


CENTAVO = Decimal("0.01")
ZERO = Decimal("0.00")


def normalizar_valor(valor: Decimal) -> Decimal:
    """Arredonda para centavos, com empate afastado de zero (RN-012)."""

    return valor.quantize(CENTAVO, rounding=ROUND_HALF_UP)


def formatar_valor(valor: Decimal) -> str:
    """Produz o formato monetário do contrato de saída."""

    return f"{normalizar_valor(valor):.2f}"


def formatar_original(valor: Decimal) -> str:
    """Preserva todas as casas decimais recebidas, sem notação científica."""

    return format(valor, "f")

