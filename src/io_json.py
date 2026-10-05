"""Leitura, validação e escrita do contrato JSON."""

from __future__ import annotations

import json
import os
import re
import tempfile
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

from src.model import Colaborador, Despesa, Periodo, Solicitacao
from src.money import normalizar_valor


COMPETENCIA_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
MOEDA_RE = re.compile(r"^[A-Za-z]{3}$")


class EntradaInvalida(ValueError):
    """Documento que não cumpre a seção 4 da spec."""

    def __init__(self, erros: list[str]) -> None:
        self.erros = tuple(erros)
        super().__init__("Entrada inválida:\n- " + "\n- ".join(erros))


def _objeto(valor: Any, caminho: str, erros: list[str]) -> dict[str, Any]:
    if not isinstance(valor, dict):
        erros.append(f"{caminho}: deve ser um objeto")
        return {}
    return valor


def _texto(objeto: dict[str, Any], campo: str, caminho: str, erros: list[str]) -> str:
    valor = objeto.get(campo)
    if not isinstance(valor, str) or not valor.strip():
        erros.append(f"{caminho}.{campo}: deve ser texto não vazio")
        return ""
    return valor


def _data(objeto: dict[str, Any], campo: str, caminho: str, erros: list[str]) -> date | None:
    valor = objeto.get(campo)
    if not isinstance(valor, str):
        erros.append(f"{caminho}.{campo}: deve ser data no formato AAAA-MM-DD")
        return None
    try:
        resultado = date.fromisoformat(valor)
    except ValueError:
        erros.append(f"{caminho}.{campo}: data inválida")
        return None
    if resultado.isoformat() != valor:
        erros.append(f"{caminho}.{campo}: deve usar o formato AAAA-MM-DD")
        return None
    return resultado


def _decimal(objeto: dict[str, Any], campo: str, caminho: str, erros: list[str]) -> Decimal | None:
    valor = objeto.get(campo)
    if isinstance(valor, bool) or not isinstance(valor, (int, Decimal)):
        erros.append(f"{caminho}.{campo}: deve ser número finito")
        return None
    resultado = Decimal(valor) if isinstance(valor, int) else valor
    if not resultado.is_finite():
        erros.append(f"{caminho}.{campo}: deve ser número finito")
        return None
    return resultado


def validar_documento(dados: Any) -> Solicitacao:
    """Valida e converte dados já decodificados em uma solicitação."""

    erros: list[str] = []
    raiz = _objeto(dados, "$", erros)
    colaborador_json = _objeto(raiz.get("colaborador"), "colaborador", erros)
    periodo_json = _objeto(raiz.get("periodo"), "periodo", erros)

    colaborador_id = _texto(colaborador_json, "id", "colaborador", erros)
    colaborador_nome = _texto(colaborador_json, "nome", "colaborador", erros)
    centro_custo = _texto(colaborador_json, "centro_custo", "colaborador", erros)

    competencia = _texto(periodo_json, "competencia", "periodo", erros)
    if competencia and not COMPETENCIA_RE.fullmatch(competencia):
        erros.append("periodo.competencia: deve usar o formato AAAA-MM")
    inicio = _data(periodo_json, "inicio", "periodo", erros)
    fim = _data(periodo_json, "fim", "periodo", erros)
    if inicio is not None and fim is not None:
        if inicio > fim:
            erros.append("periodo: inicio não pode ser posterior a fim")
        if competencia and (
            inicio.strftime("%Y-%m") != competencia
            or fim.strftime("%Y-%m") != competencia
        ):
            erros.append("periodo: inicio e fim devem pertencer à competencia")

    despesas_json = raiz.get("despesas")
    if not isinstance(despesas_json, list):
        erros.append("despesas: deve ser uma lista")
        despesas_json = []

    despesas: list[Despesa] = []
    ids: set[str] = set()
    for indice, item_bruto in enumerate(despesas_json):
        caminho = f"despesas[{indice}]"
        item = _objeto(item_bruto, caminho, erros)
        id_despesa = _texto(item, "id", caminho, erros)
        if id_despesa:
            if id_despesa in ids:
                erros.append(f"{caminho}.id: identificador repetido '{id_despesa}'")
            ids.add(id_despesa)
        data_despesa = _data(item, "data", caminho, erros)
        categoria = _texto(item, "categoria", caminho, erros)
        descricao = _texto(item, "descricao", caminho, erros)
        fornecedor = _texto(item, "fornecedor", caminho, erros)
        moeda_bruta = item.get("moeda", "BRL")
        if not isinstance(moeda_bruta, str) or not MOEDA_RE.fullmatch(
            moeda_bruta.strip()
        ):
            erros.append(f"{caminho}.moeda: deve conter três letras")
            moeda = ""
        else:
            moeda = moeda_bruta.strip().upper()
        valor = _decimal(item, "valor", caminho, erros)
        tem_nota = item.get("tem_nota_fiscal")
        if not isinstance(tem_nota, bool):
            erros.append(f"{caminho}.tem_nota_fiscal: deve ser booleano")

        if (
            id_despesa
            and data_despesa is not None
            and categoria
            and descricao
            and fornecedor
            and moeda
            and valor is not None
            and isinstance(tem_nota, bool)
        ):
            despesas.append(
                Despesa(
                    posicao=indice,
                    id=id_despesa,
                    data=data_despesa,
                    categoria=categoria,
                    descricao=descricao,
                    fornecedor=fornecedor,
                    moeda=moeda,
                    valor_original=valor,
                    valor_normalizado=normalizar_valor(valor),
                    tem_nota_fiscal=tem_nota,
                )
            )

    if erros:
        raise EntradaInvalida(erros)

    # Estes valores só podem estar ausentes quando já existe erro registrado.
    assert inicio is not None and fim is not None
    return Solicitacao(
        colaborador=Colaborador(colaborador_id, colaborador_nome, centro_custo),
        periodo=Periodo(competencia, inicio, fim),
        despesas=tuple(despesas),
    )


def carregar_solicitacao(caminho: str | Path) -> Solicitacao:
    """Lê JSON preservando decimais e valida todo o contrato de entrada."""

    try:
        with Path(caminho).open("r", encoding="utf-8") as arquivo:
            dados = json.load(
                arquivo,
                parse_float=Decimal,
                parse_constant=lambda constante: (_ for _ in ()).throw(
                    ValueError(f"número não finito: {constante}")
                ),
            )
    except (OSError, json.JSONDecodeError, UnicodeError, ValueError) as erro:
        raise EntradaInvalida([f"arquivo: {erro}"]) from erro
    return validar_documento(dados)


def gravar_resultado(caminho: str | Path, resultado: dict[str, object]) -> None:
    """Grava JSON por substituição atômica, sem deixar arquivo parcial."""

    destino = Path(caminho)
    temporario: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=destino.parent,
            prefix=f".{destino.name}.",
            suffix=".tmp",
            delete=False,
        ) as arquivo:
            temporario = Path(arquivo.name)
            json.dump(resultado, arquivo, ensure_ascii=False, indent=2)
            arquivo.write("\n")
            arquivo.flush()
            os.fsync(arquivo.fileno())
        os.replace(temporario, destino)
        temporario = None
    finally:
        if temporario is not None:
            temporario.unlink(missing_ok=True)


