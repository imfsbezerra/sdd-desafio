"""Contratos externos da Política v4 e das taxas de câmbio."""

from __future__ import annotations

import json
import re
from datetime import date
from decimal import Decimal
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

from src.io_json import EntradaInvalida
from src.model import Cambio, Politica, RegraCategoria, Solicitacao


MOEDA_RE = re.compile(r"^[A-Za-z]{3}$")


def _ler_json(caminho: str | Path, origem: str) -> Any:
    try:
        with Path(caminho).open("r", encoding="utf-8") as arquivo:
            return json.load(
                arquivo,
                parse_float=Decimal,
                parse_constant=lambda constante: (_ for _ in ()).throw(
                    ValueError(f"número não finito: {constante}")
                ),
            )
    except (OSError, json.JSONDecodeError, UnicodeError, ValueError) as erro:
        raise EntradaInvalida([f"{origem}.arquivo: {erro}"]) from erro


def _decimal(valor: Any, caminho: str, erros: list[str]) -> Decimal | None:
    if isinstance(valor, bool) or not isinstance(valor, (int, Decimal)):
        erros.append(f"{caminho}: deve ser número finito")
        return None
    resultado = Decimal(valor) if isinstance(valor, int) else valor
    if not resultado.is_finite():
        erros.append(f"{caminho}: deve ser número finito")
        return None
    return resultado


def _data(valor: Any, caminho: str, erros: list[str]) -> date | None:
    if not isinstance(valor, str):
        erros.append(f"{caminho}: deve ser data no formato AAAA-MM-DD")
        return None
    try:
        resultado = date.fromisoformat(valor)
    except ValueError:
        erros.append(f"{caminho}: data inválida")
        return None
    if resultado.isoformat() != valor:
        erros.append(f"{caminho}: deve usar o formato AAAA-MM-DD")
        return None
    return resultado


def _texto(valor: Any, caminho: str, erros: list[str]) -> str:
    if not isinstance(valor, str) or not valor.strip():
        erros.append(f"{caminho}: deve ser texto não vazio")
        return ""
    return valor.strip()


def _validar_tabela(
    valor: Any, caminho: str, erros: list[str]
) -> Mapping[str, RegraCategoria]:
    if not isinstance(valor, dict) or not valor:
        erros.append(f"{caminho}: deve ser objeto não vazio")
        return MappingProxyType({})

    tabela: dict[str, RegraCategoria] = {}
    for categoria_bruta, regra_bruta in valor.items():
        if not isinstance(categoria_bruta, str) or not categoria_bruta.strip():
            erros.append(f"{caminho}: categoria deve ser texto não vazio")
            continue
        categoria = categoria_bruta.strip().casefold()
        if categoria in tabela:
            erros.append(f"{caminho}.{categoria}: categoria repetida após normalização")
            continue
        if not isinstance(regra_bruta, dict):
            erros.append(f"{caminho}.{categoria}: deve ser objeto")
            continue
        limite = _decimal(
            regra_bruta.get("limite"), f"{caminho}.{categoria}.limite", erros
        )
        periodicidade = regra_bruta.get("periodicidade")
        if periodicidade not in {"dia", "diaria"}:
            erros.append(
                f"{caminho}.{categoria}.periodicidade: deve ser 'dia' ou 'diaria'"
            )
        if limite is not None and limite < 0:
            erros.append(f"{caminho}.{categoria}.limite: não pode ser negativo")
        if limite is not None and limite >= 0 and periodicidade in {"dia", "diaria"}:
            tabela[categoria] = RegraCategoria(limite, periodicidade)
    return MappingProxyType(tabela)


def validar_politica(dados: Any) -> Politica:
    erros: list[str] = []
    if not isinstance(dados, dict):
        raise EntradaInvalida(["politica: deve ser objeto"])

    versao = _texto(dados.get("versao"), "politica.versao", erros)
    vigencia = _data(dados.get("vigencia"), "politica.vigencia", erros)
    moeda_base = _texto(dados.get("moeda_base"), "politica.moeda_base", erros).upper()
    if moeda_base and moeda_base != "BRL":
        erros.append("politica.moeda_base: deve ser BRL")

    padrao = _validar_tabela(dados.get("padrao"), "politica.padrao", erros)
    centros_brutos = dados.get("centros_custo")
    centros: dict[str, Mapping[str, RegraCategoria]] = {}
    if not isinstance(centros_brutos, dict):
        erros.append("politica.centros_custo: deve ser objeto")
    else:
        for centro_bruto, tabela_bruta in centros_brutos.items():
            if not isinstance(centro_bruto, str) or not centro_bruto.strip():
                erros.append("politica.centros_custo: chave deve ser texto não vazio")
                continue
            centro = centro_bruto.strip()
            if centro in centros:
                erros.append(f"politica.centros_custo.{centro}: centro repetido")
                continue
            centros[centro] = _validar_tabela(
                tabela_bruta, f"politica.centros_custo.{centro}", erros
            )

    nota = _decimal(
        dados.get("nota_fiscal_obrigatoria_acima_de"),
        "politica.nota_fiscal_obrigatoria_acima_de",
        erros,
    )
    viagem = _decimal(
        dados.get("acrescimo_em_viagem_percentual"),
        "politica.acrescimo_em_viagem_percentual",
        erros,
    )
    if nota is not None and nota < 0:
        erros.append("politica.nota_fiscal_obrigatoria_acima_de: não pode ser negativo")
    if viagem is not None and viagem < 0:
        erros.append("politica.acrescimo_em_viagem_percentual: não pode ser negativo")

    if erros:
        raise EntradaInvalida(erros)
    assert vigencia is not None and nota is not None and viagem is not None
    return Politica(
        versao=versao,
        vigencia=vigencia,
        moeda_base=moeda_base,
        padrao=padrao,
        centros_custo=MappingProxyType(centros),
        nota_fiscal_acima_de=nota,
        acrescimo_viagem_percentual=viagem,
    )


def carregar_politica(caminho: str | Path) -> Politica:
    return validar_politica(_ler_json(caminho, "politica"))


def validar_cambio(dados: Any) -> Cambio:
    erros: list[str] = []
    if not isinstance(dados, dict):
        raise EntradaInvalida(["cambio: deve ser objeto"])
    moeda_base = _texto(dados.get("moeda_base"), "cambio.moeda_base", erros).upper()
    if moeda_base and moeda_base != "BRL":
        erros.append("cambio.moeda_base: deve ser BRL")

    taxas_brutas = dados.get("taxas")
    taxas: dict[date, Mapping[str, Decimal]] = {}
    if not isinstance(taxas_brutas, dict) or not taxas_brutas:
        erros.append("cambio.taxas: deve ser objeto não vazio")
    else:
        for data_bruta, moedas_brutas in taxas_brutas.items():
            data_taxa = _data(data_bruta, f"cambio.taxas.{data_bruta}", erros)
            if not isinstance(moedas_brutas, dict) or not moedas_brutas:
                erros.append(f"cambio.taxas.{data_bruta}: deve ser objeto não vazio")
                continue
            moedas: dict[str, Decimal] = {}
            for moeda_bruta, taxa_bruta in moedas_brutas.items():
                if not isinstance(moeda_bruta, str) or not MOEDA_RE.fullmatch(moeda_bruta):
                    erros.append(
                        f"cambio.taxas.{data_bruta}: moeda deve ter três letras"
                    )
                    continue
                moeda = moeda_bruta.upper()
                taxa = _decimal(
                    taxa_bruta, f"cambio.taxas.{data_bruta}.{moeda}", erros
                )
                if taxa is not None and taxa <= 0:
                    erros.append(
                        f"cambio.taxas.{data_bruta}.{moeda}: deve ser maior que zero"
                    )
                if taxa is not None and taxa > 0:
                    moedas[moeda] = taxa
            if data_taxa is not None:
                taxas[data_taxa] = MappingProxyType(moedas)

    if erros:
        raise EntradaInvalida(erros)
    return Cambio(moeda_base=moeda_base, taxas=MappingProxyType(taxas))


def carregar_cambio(caminho: str | Path) -> Cambio:
    return validar_cambio(_ler_json(caminho, "cambio"))


def validar_vigencia(solicitacao: Solicitacao, politica: Politica) -> None:
    if solicitacao.periodo.inicio < politica.vigencia:
        raise EntradaInvalida(
            [
                "periodo.inicio: período começa antes da vigência "
                f"{politica.vigencia.isoformat()} da política"
            ]
        )

