"""Interface de linha de comando do motor."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from src.engine import processar_solicitacao
from src.io_json import EntradaInvalida, carregar_solicitacao, gravar_resultado


def criar_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="reembolso")
    comandos = parser.add_subparsers(dest="comando", required=True)
    calcular = comandos.add_parser("calcular", help="calcula reembolso de despesas")
    calcular.add_argument("--input", required=True, help="arquivo JSON de entrada")
    calcular.add_argument("--output", required=True, help="arquivo JSON de saída")
    return parser


def main(argumentos: Sequence[str] | None = None) -> int:
    args = criar_parser().parse_args(argumentos)
    try:
        solicitacao = carregar_solicitacao(args.input)
        resultado = processar_solicitacao(solicitacao)
        gravar_resultado(args.output, resultado)
    except EntradaInvalida as erro:
        print(erro, file=sys.stderr)
        return 2
    except OSError as erro:
        print(f"Falha operacional: {erro}", file=sys.stderr)
        return 1

    print(f"Resultado gravado em {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

