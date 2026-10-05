import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path

from src.config import (
    carregar_cambio,
    carregar_politica,
    validar_cambio,
    validar_politica,
    validar_vigencia,
)
from src.io_json import EntradaInvalida
from tests.builders import criar_solicitacao


RAIZ = Path(__file__).resolve().parents[1]
ENVELOPE = RAIZ / "exemplos" / "envelope"


def politica_minima() -> dict:
    return {
        "versao": "v4",
        "vigencia": "2026-07-01",
        "moeda_base": "BRL",
        "padrao": {
            "alimentacao": {"limite": Decimal("60"), "periodicidade": "dia"}
        },
        "centros_custo": {},
        "nota_fiscal_obrigatoria_acima_de": Decimal("100"),
        "acrescimo_em_viagem_percentual": Decimal("50"),
    }


class ConfigTests(unittest.TestCase):
    def test_rn001_carrega_fontes_v4(self) -> None:
        politica = carregar_politica(ENVELOPE / "politica-v4.json")
        cambio = carregar_cambio(ENVELOPE / "cambio.json")

        self.assertEqual(politica.versao, "v4")
        self.assertEqual(
            politica.centros_custo["CC-COMERCIAL"]["representacao"].limite,
            Decimal("300.00"),
        )
        self.assertEqual(cambio.taxas[date(2026, 7, 14)]["EUR"], Decimal("5.93"))

    def test_rn001_rejeita_politica_invalida(self) -> None:
        dados = politica_minima()
        dados["padrao"]["alimentacao"]["periodicidade"] = "mes"

        with self.assertRaisesRegex(EntradaInvalida, "periodicidade"):
            validar_politica(dados)

    def test_rn001_rejeita_cambio_invalido(self) -> None:
        dados = {
            "moeda_base": "BRL",
            "taxas": {"2026-07-14": {"EUR": Decimal("0")}},
        }

        with self.assertRaisesRegex(EntradaInvalida, "maior que zero"):
            validar_cambio(dados)

    def test_rn002_rejeita_periodo_anterior_a_vigencia(self) -> None:
        politica = validar_politica(politica_minima())
        solicitacao = criar_solicitacao(
            {"data": "2026-06-30"},
            periodo={
                "competencia": "2026-06",
                "inicio": "2026-06-01",
                "fim": "2026-06-30",
            },
        )

        with self.assertRaisesRegex(EntradaInvalida, "antes da vigência"):
            validar_vigencia(solicitacao, politica)


if __name__ == "__main__":
    unittest.main()

