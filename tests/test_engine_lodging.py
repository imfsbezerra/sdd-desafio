import unittest
from decimal import Decimal

from src.engine import aplicar_limite_hospedagem
from src.model import Status
from tests.builders import criar_solicitacao


class HospedagemTests(unittest.TestCase):
    def test_rn009_cada_item_e_uma_diaria(self) -> None:
        despesa = criar_solicitacao(
            {
                "categoria": "hospedagem",
                "descricao": "Hotel Rio - 2 diárias",
                "valor": Decimal("480.00"),
            }
        ).despesas[0]

        decisao = aplicar_limite_hospedagem(despesa)

        self.assertEqual(decisao.status, Status.PARCIAL)
        self.assertEqual(decisao.valor_reembolsavel, Decimal("250.00"))

    def test_amb006_nao_extrai_noites_da_descricao(self) -> None:
        for descricao in ("Hotel", "Hotel - 2 diárias", "Airbnb 3 noites"):
            with self.subTest(descricao=descricao):
                despesa = criar_solicitacao(
                    {
                        "categoria": "hospedagem",
                        "descricao": descricao,
                        "valor": Decimal("690.00"),
                    }
                ).despesas[0]
                decisao = aplicar_limite_hospedagem(despesa)
                self.assertEqual(decisao.valor_reembolsavel, Decimal("250.00"))

    def test_hospedagens_na_mesma_data_tem_limites_independentes(self) -> None:
        solicitacao = criar_solicitacao(
            {
                "categoria": "hospedagem",
                "descricao": "Hotel A",
                "valor": Decimal("300.00"),
            },
            {
                "categoria": "hospedagem",
                "descricao": "Hotel B",
                "valor": Decimal("300.00"),
            },
        )

        decisoes = [aplicar_limite_hospedagem(item) for item in solicitacao.despesas]
        self.assertEqual(
            [item.valor_reembolsavel for item in decisoes],
            [Decimal("250.00"), Decimal("250.00")],
        )

    def test_hospedagem_dentro_do_limite_e_aprovada(self) -> None:
        despesa = criar_solicitacao(
            {"categoria": "hospedagem", "valor": Decimal("240.00")}
        ).despesas[0]

        decisao = aplicar_limite_hospedagem(despesa)
        self.assertEqual(decisao.status, Status.APROVADA)
        self.assertEqual(decisao.valor_reembolsavel, Decimal("240.00"))


if __name__ == "__main__":
    unittest.main()

