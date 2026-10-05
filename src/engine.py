"""Núcleo puro das regras de reembolso."""

from __future__ import annotations

from decimal import Decimal

from src.model import Decisao, Despesa, Periodo, Status
from src.money import ZERO


CATEGORIAS = frozenset({"alimentacao", "transporte_urbano", "hospedagem"})
LIMITES_BASE = {
    "alimentacao": Decimal("60.00"),
    "transporte_urbano": Decimal("80.00"),
    "hospedagem": Decimal("250.00"),
}
LIMITE_NOTA_FISCAL = Decimal("100.00")


def texto_canonico(texto: str) -> str:
    """Ignora somente espaços externos e capitalização."""

    return texto.strip().casefold()


def categoria_canonica(despesa: Despesa) -> str:
    return texto_canonico(despesa.categoria)


def limite_base(categoria: str) -> Decimal:
    """Retorna limites sem ampliação, pois a entrada não informa viagem."""

    return LIMITES_BASE[categoria]


def _parte_positiva(despesa: Despesa) -> Decimal:
    return max(despesa.valor_normalizado, ZERO)


def rejeitar(
    despesa: Despesa,
    codigo: str,
    justificativa: str,
    regras: tuple[str, ...],
) -> Decisao:
    return Decisao(
        id=despesa.id,
        status=Status.REJEITADA,
        valor_original=despesa.valor_original,
        valor_normalizado=despesa.valor_normalizado,
        valor_reembolsavel=ZERO,
        valor_nao_reembolsavel=_parte_positiva(despesa),
        codigo_motivo=codigo,
        justificativa=justificativa,
        regras_aplicadas=regras,
    )


def avaliar_elegibilidade_basica(
    despesa: Despesa, periodo: Periodo
) -> Decisao | None:
    """Aplica RN-002 a RN-004 na precedência definida pela spec."""

    if not (periodo.inicio <= despesa.data <= periodo.fim):
        return rejeitar(
            despesa,
            "FORA_DA_COMPETENCIA",
            (
                f"Despesa em {despesa.data.isoformat()} fora do período "
                f"{periodo.inicio.isoformat()} a {periodo.fim.isoformat()}."
            ),
            ("RN-002",),
        )

    categoria = categoria_canonica(despesa)
    if categoria not in CATEGORIAS:
        return rejeitar(
            despesa,
            "CATEGORIA_NAO_COBERTA",
            f"Categoria '{despesa.categoria}' não coberta pela política.",
            ("RN-003",),
        )

    if despesa.valor_normalizado <= ZERO:
        return rejeitar(
            despesa,
            "VALOR_NAO_POSITIVO",
            "Valor igual a zero ou negativo não é reembolsável.",
            ("RN-004",),
        )

    return None


def assinatura_duplicidade(despesa: Despesa) -> tuple[object, ...]:
    """Identidade de negócio definida por RN-006."""

    return (
        despesa.data,
        categoria_canonica(despesa),
        texto_canonico(despesa.descricao),
        texto_canonico(despesa.fornecedor),
        despesa.valor_normalizado,
    )


def avaliar_duplicata_e_nota(
    despesa: Despesa, assinaturas_vistas: set[tuple[object, ...]]
) -> Decisao | None:
    """Aplica RN-006 antes de RN-005, conforme a seção 9 da spec."""

    assinatura = assinatura_duplicidade(despesa)
    if assinatura in assinaturas_vistas:
        return rejeitar(
            despesa,
            "DUPLICATA",
            "Lançamento posterior repete data, categoria, descrição, fornecedor e valor.",
            ("RN-006",),
        )

    # A primeira ocorrência reserva a assinatura mesmo se falhar depois por nota.
    assinaturas_vistas.add(assinatura)
    if despesa.valor_normalizado > LIMITE_NOTA_FISCAL and not despesa.tem_nota_fiscal:
        return rejeitar(
            despesa,
            "NOTA_FISCAL_AUSENTE",
            (
                f"Nota fiscal obrigatória para valor solicitado de "
                f"R$ {despesa.valor_normalizado:.2f}."
            ),
            ("RN-005",),
        )

    return None


