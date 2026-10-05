import unittest
from decimal import Decimal

from src.engine import assinatura_duplicidade, avaliar_duplicata_e_nota
from tests.builders import criar_solicitacao


class DuplicataENotaTests(unittest.TestCase):
    def test_rn005_fronteira_nota(self) -> None:
        cem = criar_solicitacao(
            {"valor": Decimal("100.00"), "tem_nota_fiscal": False}
        ).despesas[0]
        acima = criar_solicitacao(
            {"valor": Decimal("100.01"), "tem_nota_fiscal": False}
        ).despesas[0]

        self.assertIsNone(avaliar_duplicata_e_nota(cem, set()))
        decisao = avaliar_duplicata_e_nota(acima, set())
        self.assertEqual(decisao.codigo_motivo, "NOTA_FISCAL_AUSENTE")

    def test_rn005_usa_valor_normalizado_solicitado(self) -> None:
        despesa = criar_solicitacao(
            {"valor": Decimal("100.005"), "tem_nota_fiscal": False}
        ).despesas[0]

        decisao = avaliar_duplicata_e_nota(despesa, set())
        self.assertEqual(despesa.valor_normalizado, Decimal("100.01"))
        self.assertEqual(decisao.codigo_motivo, "NOTA_FISCAL_AUSENTE")

    def test_rn006_primeira_ocorrencia(self) -> None:
        solicitacao = criar_solicitacao(
            {"descricao": "Almoço"},
            {"descricao": "Almoço"},
        )
        vistas: set[tuple[object, ...]] = set()

        primeira = avaliar_duplicata_e_nota(solicitacao.despesas[0], vistas)
        segunda = avaliar_duplicata_e_nota(solicitacao.despesas[1], vistas)

        self.assertIsNone(primeira)
        self.assertEqual(segunda.codigo_motivo, "DUPLICATA")

    def test_amb007_normaliza_assinatura(self) -> None:
        solicitacao = criar_solicitacao(
            {
                "categoria": " ALIMENTACAO ",
                "descricao": " ALMOÇO ",
                "fornecedor": " RESTAURANTE ",
            },
            {
                "categoria": "alimentacao",
                "descricao": "almoço",
                "fornecedor": "restaurante",
            },
        )

        self.assertEqual(
            assinatura_duplicidade(solicitacao.despesas[0]),
            assinatura_duplicidade(solicitacao.despesas[1]),
        )

    def test_amb015_duplicata_precede_nota(self) -> None:
        solicitacao = criar_solicitacao(
            {
                "descricao": "Hotel",
                "valor": Decimal("200.00"),
                "tem_nota_fiscal": False,
            },
            {
                "descricao": "Hotel",
                "valor": Decimal("200.00"),
                "tem_nota_fiscal": False,
            },
        )
        vistas: set[tuple[object, ...]] = set()

        primeira = avaliar_duplicata_e_nota(solicitacao.despesas[0], vistas)
        segunda = avaliar_duplicata_e_nota(solicitacao.despesas[1], vistas)

        self.assertEqual(primeira.codigo_motivo, "NOTA_FISCAL_AUSENTE")
        self.assertEqual(segunda.codigo_motivo, "DUPLICATA")


if __name__ == "__main__":
    unittest.main()

