"""Núcleo puro das regras de reembolso."""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal

from src.model import (
    Conversao,
    Decisao,
    Despesa,
    Periodo,
    Politica,
    RegraCategoria,
    Solicitacao,
    Status,
)
from src.money import ZERO, formatar_original, formatar_valor


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


def aplicar_limite_diario(
    despesa: Despesa, saldos: dict[tuple[object, str], Decimal]
) -> Decisao:
    """Consome o saldo de alimentação ou transporte na ordem recebida."""

    categoria = categoria_canonica(despesa)
    if categoria not in {"alimentacao", "transporte_urbano"}:
        raise ValueError(f"categoria sem limite diário: {categoria}")

    chave = (despesa.data, categoria)
    saldo = saldos.setdefault(chave, limite_base(categoria))
    reembolsavel = min(despesa.valor_normalizado, saldo)
    saldos[chave] = saldo - reembolsavel
    regra_limite = "RN-007" if categoria == "alimentacao" else "RN-008"
    limite = limite_base(categoria)

    if reembolsavel == despesa.valor_normalizado:
        return Decisao(
            id=despesa.id,
            status=Status.APROVADA,
            valor_original=despesa.valor_original,
            valor_normalizado=despesa.valor_normalizado,
            valor_reembolsavel=reembolsavel,
            valor_nao_reembolsavel=ZERO,
            codigo_motivo="APROVADA_INTEGRAL",
            justificativa=(
                f"Valor integral dentro do limite diário de R$ {limite:.2f} "
                f"para {categoria} em {despesa.data.isoformat()}."
            ),
            regras_aplicadas=(regra_limite,),
        )

    if reembolsavel > ZERO:
        return Decisao(
            id=despesa.id,
            status=Status.PARCIAL,
            valor_original=despesa.valor_original,
            valor_normalizado=despesa.valor_normalizado,
            valor_reembolsavel=reembolsavel,
            valor_nao_reembolsavel=despesa.valor_normalizado - reembolsavel,
            codigo_motivo="LIMITE_PARCIAL",
            justificativa=(
                f"Reembolso limitado ao saldo de R$ {reembolsavel:.2f} para "
                f"{categoria} em {despesa.data.isoformat()}."
            ),
            regras_aplicadas=(regra_limite, "RN-010"),
        )

    return rejeitar(
        despesa,
        "LIMITE_ESGOTADO",
        (
            f"Limite diário de R$ {limite:.2f} para {categoria} em "
            f"{despesa.data.isoformat()} já foi consumido."
        ),
        (regra_limite, "RN-010"),
    )


def aplicar_limite_hospedagem(despesa: Despesa) -> Decisao:
    """Aplica uma diária por lançamento, sem interpretar texto livre."""

    if categoria_canonica(despesa) != "hospedagem":
        raise ValueError("despesa não pertence à categoria hospedagem")

    limite = limite_base("hospedagem")
    reembolsavel = min(despesa.valor_normalizado, limite)
    if reembolsavel == despesa.valor_normalizado:
        return Decisao(
            id=despesa.id,
            status=Status.APROVADA,
            valor_original=despesa.valor_original,
            valor_normalizado=despesa.valor_normalizado,
            valor_reembolsavel=reembolsavel,
            valor_nao_reembolsavel=ZERO,
            codigo_motivo="APROVADA_INTEGRAL",
            justificativa="Valor integral dentro do limite de R$ 250,00 por diária.",
            regras_aplicadas=("RN-009",),
        )

    return Decisao(
        id=despesa.id,
        status=Status.PARCIAL,
        valor_original=despesa.valor_original,
        valor_normalizado=despesa.valor_normalizado,
        valor_reembolsavel=reembolsavel,
        valor_nao_reembolsavel=despesa.valor_normalizado - reembolsavel,
        codigo_motivo="LIMITE_PARCIAL",
        justificativa="Reembolso limitado a R$ 250,00 para uma diária de hospedagem.",
        regras_aplicadas=("RN-009", "RN-010"),
    )


def processar_solicitacao(solicitacao: Solicitacao) -> dict[str, object]:
    """Executa a precedência completa e monta o contrato de saída."""

    decisoes: list[Decisao] = []
    assinaturas: set[tuple[object, ...]] = set()
    saldos: dict[tuple[object, str], Decimal] = {}

    for despesa in solicitacao.despesas:
        decisao = avaliar_elegibilidade_basica(despesa, solicitacao.periodo)
        if decisao is None:
            decisao = avaliar_duplicata_e_nota(despesa, assinaturas)
        if decisao is None:
            categoria = categoria_canonica(despesa)
            if categoria == "hospedagem":
                decisao = aplicar_limite_hospedagem(despesa)
            else:
                decisao = aplicar_limite_diario(despesa, saldos)
        decisoes.append(decisao)

    total_solicitado = sum(
        (max(item.valor_normalizado, ZERO) for item in solicitacao.despesas),
        start=ZERO,
    )
    total_reembolsavel = sum(
        (item.valor_reembolsavel for item in decisoes), start=ZERO
    )
    total_nao_reembolsavel = total_solicitado - total_reembolsavel

    return {
        "politica_versao": "3",
        "colaborador": {
            "id": solicitacao.colaborador.id,
            "nome": solicitacao.colaborador.nome,
            "centro_custo": solicitacao.colaborador.centro_custo,
        },
        "periodo": {
            "competencia": solicitacao.periodo.competencia,
            "inicio": solicitacao.periodo.inicio.isoformat(),
            "fim": solicitacao.periodo.fim.isoformat(),
        },
        "resumo": {
            "quantidade_despesas": len(solicitacao.despesas),
            "total_solicitado": formatar_valor(total_solicitado),
            "total_reembolsavel": formatar_valor(total_reembolsavel),
            "total_nao_reembolsavel": formatar_valor(total_nao_reembolsavel),
            "quantidade_aprovadas": sum(
                item.status is Status.APROVADA for item in decisoes
            ),
            "quantidade_parciais": sum(
                item.status is Status.PARCIAL for item in decisoes
            ),
            "quantidade_rejeitadas": sum(
                item.status is Status.REJEITADA for item in decisoes
            ),
        },
        "decisoes": [_serializar_decisao(item) for item in decisoes],
    }


def _serializar_decisao(decisao: Decisao) -> dict[str, object]:
    return {
        "id": decisao.id,
        "status": decisao.status.value,
        "valor_original": formatar_original(decisao.valor_original),
        "valor_normalizado": formatar_valor(decisao.valor_normalizado),
        "valor_reembolsavel": formatar_valor(decisao.valor_reembolsavel),
        "valor_nao_reembolsavel": formatar_valor(decisao.valor_nao_reembolsavel),
        "codigo_motivo": decisao.codigo_motivo,
        "justificativa": decisao.justificativa,
        "regras_aplicadas": list(decisao.regras_aplicadas),
    }


def selecionar_tabela(
    politica: Politica, centro_custo: str
) -> tuple[str, Mapping[str, RegraCategoria]]:
    """Seleciona centro conhecido ou a tabela padrão inteira (RN-003)."""

    if centro_custo in politica.centros_custo:
        return "centro_custo", politica.centros_custo[centro_custo]
    return "padrao", politica.padrao


def assinatura_duplicidade_v4(despesa: Despesa) -> tuple[object, ...]:
    return (
        despesa.data,
        categoria_canonica(despesa),
        texto_canonico(despesa.descricao),
        texto_canonico(despesa.fornecedor),
        despesa.moeda,
        despesa.valor_normalizado,
    )


def _rejeitar_v4(
    despesa: Despesa,
    conversao: Conversao,
    codigo: str,
    justificativa: str,
    regras: tuple[str, ...],
) -> Decisao:
    valor_brl = conversao.valor_brl
    nao_reembolsavel = (
        max(valor_brl, ZERO) if valor_brl is not None else ZERO
    )
    return Decisao(
        id=despesa.id,
        status=Status.REJEITADA,
        valor_original=despesa.valor_original,
        valor_normalizado=despesa.valor_normalizado,
        valor_reembolsavel=ZERO,
        valor_nao_reembolsavel=nao_reembolsavel,
        codigo_motivo=codigo,
        justificativa=justificativa,
        regras_aplicadas=regras,
        moeda_original=despesa.moeda,
        taxa_cambio=conversao.taxa,
        data_taxa_cambio=conversao.data_taxa,
        valor_convertido_brl=valor_brl,
    )


def avaliar_politica_e_documentos_v4(
    despesa: Despesa,
    conversao: Conversao,
    tabela: Mapping[str, RegraCategoria],
    politica: Politica,
    assinaturas_vistas: set[tuple[object, ...]],
) -> tuple[Decisao | None, RegraCategoria | None]:
    """Aplica categoria, valor, duplicidade e nota conforme a Política v4."""

    categoria = categoria_canonica(despesa)
    regra = tabela.get(categoria)
    if regra is None:
        return (
            _rejeitar_v4(
                despesa,
                conversao,
                "CATEGORIA_NAO_COBERTA",
                f"Categoria '{despesa.categoria}' ausente da tabela selecionada.",
                ("RN-004",),
            ),
            None,
        )
    if regra.limite == ZERO:
        return (
            _rejeitar_v4(
                despesa,
                conversao,
                "CATEGORIA_NAO_REEMBOLSAVEL",
                f"Categoria '{categoria}' possui limite R$ 0,00 para o centro de custo.",
                ("RN-004",),
            ),
            None,
        )
    if despesa.valor_normalizado <= ZERO:
        return (
            _rejeitar_v4(
                despesa,
                conversao,
                "VALOR_NAO_POSITIVO",
                "Valor igual a zero ou negativo não é reembolsável.",
                ("RN-009",),
            ),
            None,
        )

    assinatura = assinatura_duplicidade_v4(despesa)
    if assinatura in assinaturas_vistas:
        return (
            _rejeitar_v4(
                despesa,
                conversao,
                "DUPLICATA",
                "Lançamento posterior repete a transação na mesma moeda.",
                ("RN-011",),
            ),
            None,
        )
    assinaturas_vistas.add(assinatura)

    assert conversao.valor_brl is not None
    if (
        conversao.valor_brl > politica.nota_fiscal_acima_de
        and not despesa.tem_nota_fiscal
    ):
        return (
            _rejeitar_v4(
                despesa,
                conversao,
                "NOTA_FISCAL_AUSENTE",
                (
                    "Nota fiscal obrigatória para valor convertido de "
                    f"R$ {conversao.valor_brl:.2f}."
                ),
                ("RN-010",),
            ),
            None,
        )
    return None, regra


def aplicar_limite_v4(
    despesa: Despesa,
    conversao: Conversao,
    regra: RegraCategoria,
    saldos: dict[tuple[object, str], Decimal],
) -> Decisao:
    """Aplica periodicidade e limite fornecidos pela tabela externa."""

    assert conversao.valor_brl is not None
    categoria = categoria_canonica(despesa)
    if regra.periodicidade == "dia":
        chave = (despesa.data, categoria)
        saldo = saldos.setdefault(chave, regra.limite)
        reembolsavel = min(conversao.valor_brl, saldo)
        saldos[chave] = saldo - reembolsavel
    else:
        reembolsavel = min(conversao.valor_brl, regra.limite)

    comum = {
        "id": despesa.id,
        "valor_original": despesa.valor_original,
        "valor_normalizado": despesa.valor_normalizado,
        "moeda_original": despesa.moeda,
        "taxa_cambio": conversao.taxa,
        "data_taxa_cambio": conversao.data_taxa,
        "valor_convertido_brl": conversao.valor_brl,
    }
    if reembolsavel == conversao.valor_brl:
        return Decisao(
            **comum,
            status=Status.APROVADA,
            valor_reembolsavel=reembolsavel,
            valor_nao_reembolsavel=ZERO,
            codigo_motivo="APROVADA_INTEGRAL",
            justificativa=(
                f"Valor integral dentro do limite de R$ {regra.limite:.2f} "
                f"por {regra.periodicidade}."
            ),
            regras_aplicadas=("RN-012",),
        )
    if reembolsavel > ZERO:
        return Decisao(
            **comum,
            status=Status.PARCIAL,
            valor_reembolsavel=reembolsavel,
            valor_nao_reembolsavel=conversao.valor_brl - reembolsavel,
            codigo_motivo="LIMITE_PARCIAL",
            justificativa=(
                f"Reembolso limitado a R$ {reembolsavel:.2f} pela tabela externa."
            ),
            regras_aplicadas=("RN-012", "RN-013"),
        )
    return _rejeitar_v4(
        despesa,
        conversao,
        "LIMITE_ESGOTADO",
        f"Limite de R$ {regra.limite:.2f} já consumido para a data e categoria.",
        ("RN-012", "RN-013"),
    )





