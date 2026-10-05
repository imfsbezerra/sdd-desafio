import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path

from src.config import carregar_cambio
from src.exchange import converter_para_brl
from src.io_json import EntradaInvalida, validar_documento
from tests.builders import criar_solicitacao


RAIZ = Path(__file__).resolve().parents[1]
CAMBIO = carregar_cambio(RAIZ / "exemplos" / "envelope" / "cambio.json")


class ExchangeTests(unittest.TestCase):
    def test_rn005_moeda_ausente_assume_brl(self) -> None:
        despesa = criar_solicitacao({"valor": Decimal("10")}).despesas[0]
        conversao = converter_para_brl(despesa, CAMBIO)

        self.assertEqual(despesa.moeda, "BRL")
        self.assertEqual(conversao.taxa, Decimal("1"))
        self.assertEqual(conversao.valor_brl, Decimal("10.00"))

    def test_rn005_normaliza_codigo_da_moeda(self) -> None:
        despesa = criar_solicitacao({"moeda": " eur "}).despesas[0]
        self.assertEqual(despesa.moeda, "EUR")

    def test_rn005_rejeita_codigo_invalido(self) -> None:
        dados = {
            "colaborador": {"id": "c", "nome": "N", "centro_custo": "CC"},
            "periodo": {
                "competencia": "2026-07",
                "inicio": "2026-07-01",
                "fim": "2026-07-31",
            },
            "despesas": [
                {
                    "id": "d",
                    "data": "2026-07-14",
                    "categoria": "alimentacao",
                    "descricao": "x",
                    "fornecedor": "y",
                    "valor": Decimal("1"),
                    "moeda": "EURO",
                    "tem_nota_fiscal": True,
                }
            ],
        }
        with self.assertRaisesRegex(EntradaInvalida, "três letras"):
            validar_documento(dados)

    def test_rn006_converte_eur(self) -> None:
        despesa = criar_solicitacao(
            {"data": "2026-07-14", "valor": Decimal("22"), "moeda": "EUR"}
        ).despesas[0]

        conversao = converter_para_brl(despesa, CAMBIO)

        self.assertEqual(conversao.taxa, Decimal("5.93"))
        self.assertEqual(conversao.data_taxa, date(2026, 7, 14))
        self.assertEqual(conversao.valor_brl, Decimal("130.46"))

    def test_rn007_usa_taxa_anterior(self) -> None:
        despesa = criar_solicitacao(
            {"data": "2026-07-18", "valor": Decimal("30"), "moeda": "EUR"}
        ).despesas[0]

        conversao = converter_para_brl(despesa, CAMBIO)

        self.assertEqual(conversao.taxa, Decimal("5.96"))
        self.assertEqual(conversao.data_taxa, date(2026, 7, 17))
        self.assertEqual(conversao.valor_brl, Decimal("178.80"))

    def test_rn008_rejeita_moeda_sem_cotacao(self) -> None:
        despesa = criar_solicitacao(
            {"data": "2026-07-21", "valor": Decimal("55"), "moeda": "GBP"}
        ).despesas[0]

        conversao = converter_para_brl(despesa, CAMBIO)

        self.assertIsNone(conversao.taxa)
        self.assertIsNone(conversao.data_taxa)
        self.assertIsNone(conversao.valor_brl)

    def test_rn015_arredonda_brl(self) -> None:
        despesa = criar_solicitacao(
            {"data": "2026-07-14", "valor": Decimal("1.005"), "moeda": "EUR"}
        ).despesas[0]

        conversao = converter_para_brl(despesa, CAMBIO)

        # Primeiro 1.005 EUR -> 1.01 EUR; depois 1.01 * 5.93 = 5.9893 -> 5.99 BRL.
        self.assertEqual(despesa.valor_normalizado, Decimal("1.01"))
        self.assertEqual(conversao.valor_brl, Decimal("5.99"))


if __name__ == "__main__":
    unittest.main()

