import unittest
from decimal import Decimal

from src.engine import aplicar_limite_diario
from src.model import Status
from tests.builders import criar_solicitacao


class LimitesDiariosTests(unittest.TestCase):
    def test_rn007_limite_alimentacao_compartilhado(self) -> None:
        solicitacao = criar_solicitacao(
            {"valor": Decimal("72.50"), "descricao": "Almoço"},
            {"valor": Decimal("38.00"), "descricao": "Jantar"},
        )
        saldos = {}

        primeira = aplicar_limite_diario(solicitacao.despesas[0], saldos)
        segunda = aplicar_limite_diario(solicitacao.despesas[1], saldos)

        self.assertEqual(primeira.status, Status.PARCIAL)
        self.assertEqual(primeira.valor_reembolsavel, Decimal("60.00"))
        self.assertEqual(segunda.status, Status.REJEITADA)
        self.assertEqual(segunda.valor_reembolsavel, Decimal("0.00"))

    def test_rn008_limite_transporte_por_data(self) -> None:
        solicitacao = criar_solicitacao(
            {
                "categoria": "transporte_urbano",
                "data": "2026-07-03",
                "valor": Decimal("100.00"),
            },
            {
                "categoria": "transporte_urbano",
                "data": "2026-07-04",
                "valor": Decimal("100.00"),
            },
        )
        saldos = {}

        decisoes = [aplicar_limite_diario(item, saldos) for item in solicitacao.despesas]

        self.assertEqual(
            [decisao.valor_reembolsavel for decisao in decisoes],
            [Decimal("80.00"), Decimal("80.00")],
        )

    def test_rn010_aloca_na_ordem_de_entrada(self) -> None:
        solicitacao = criar_solicitacao(
            {"valor": Decimal("40.00"), "descricao": "Primeira"},
            {"valor": Decimal("40.00"), "descricao": "Segunda"},
        )
        saldos = {}

        primeira = aplicar_limite_diario(solicitacao.despesas[0], saldos)
        segunda = aplicar_limite_diario(solicitacao.despesas[1], saldos)

        self.assertEqual(primeira.valor_reembolsavel, Decimal("40.00"))
        self.assertEqual(segunda.valor_reembolsavel, Decimal("20.00"))
        self.assertEqual(segunda.status, Status.PARCIAL)

    def test_limites_de_categorias_nao_compartilham_saldo(self) -> None:
        solicitacao = criar_solicitacao(
            {"categoria": "alimentacao", "valor": Decimal("60.00")},
            {"categoria": "transporte_urbano", "valor": Decimal("80.00")},
        )
        saldos = {}

        decisoes = [aplicar_limite_diario(item, saldos) for item in solicitacao.despesas]

        self.assertTrue(all(item.status is Status.APROVADA for item in decisoes))


if __name__ == "__main__":
    unittest.main()

