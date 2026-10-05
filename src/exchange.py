"""Conversão determinística de despesas para a moeda-base BRL."""

from datetime import date
from decimal import Decimal

from src.model import Cambio, Conversao, Despesa
from src.money import normalizar_valor


def converter_para_brl(despesa: Despesa, cambio: Cambio) -> Conversao:
    """Converte pela taxa da data ou pela última taxa anterior disponível."""

    if despesa.moeda == cambio.moeda_base:
        return Conversao(
            moeda_original=despesa.moeda,
            taxa=Decimal("1"),
            data_taxa=despesa.data,
            valor_brl=despesa.valor_normalizado,
        )

    datas = [
        data_taxa
        for data_taxa, taxas in cambio.taxas.items()
        if data_taxa <= despesa.data and despesa.moeda in taxas
    ]
    if not datas:
        return Conversao(despesa.moeda, None, None, None)

    data_taxa = max(datas)
    taxa = cambio.taxas[data_taxa][despesa.moeda]
    return Conversao(
        moeda_original=despesa.moeda,
        taxa=taxa,
        data_taxa=data_taxa,
        valor_brl=normalizar_valor(despesa.valor_normalizado * taxa),
    )

