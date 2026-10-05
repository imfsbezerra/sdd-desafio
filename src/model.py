"""Estruturas de domínio independentes das fronteiras de arquivo e CLI."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import StrEnum
from typing import Mapping


class Status(StrEnum):
    APROVADA = "APROVADA"
    PARCIAL = "PARCIAL"
    REJEITADA = "REJEITADA"


@dataclass(frozen=True)
class Colaborador:
    id: str
    nome: str
    centro_custo: str


@dataclass(frozen=True)
class Periodo:
    competencia: str
    inicio: date
    fim: date


@dataclass(frozen=True)
class Despesa:
    posicao: int
    id: str
    data: date
    categoria: str
    descricao: str
    fornecedor: str
    valor_original: Decimal
    valor_normalizado: Decimal
    tem_nota_fiscal: bool


@dataclass(frozen=True)
class Solicitacao:
    colaborador: Colaborador
    periodo: Periodo
    despesas: tuple[Despesa, ...]


@dataclass(frozen=True)
class Decisao:
    id: str
    status: Status
    valor_original: Decimal
    valor_normalizado: Decimal
    valor_reembolsavel: Decimal
    valor_nao_reembolsavel: Decimal
    codigo_motivo: str
    justificativa: str
    regras_aplicadas: tuple[str, ...]


@dataclass(frozen=True)
class RegraCategoria:
    limite: Decimal
    periodicidade: str


@dataclass(frozen=True)
class Politica:
    versao: str
    vigencia: date
    moeda_base: str
    padrao: Mapping[str, RegraCategoria]
    centros_custo: Mapping[str, Mapping[str, RegraCategoria]]
    nota_fiscal_acima_de: Decimal
    acrescimo_viagem_percentual: Decimal


@dataclass(frozen=True)
class Cambio:
    moeda_base: str
    taxas: Mapping[date, Mapping[str, Decimal]]

