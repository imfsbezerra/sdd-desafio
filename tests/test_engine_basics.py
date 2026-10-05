import unittest
from decimal import Decimal

from src.engine import avaliar_elegibilidade_basica, limite_base
from tests.builders import criar_solicitacao


class ElegibilidadeBasicaTests(unittest.TestCase):
    def _avaliar(self, **alteracoes):
        solicitacao = criar_solicitacao(alteracoes)
        return avaliar_elegibilidade_basica(
            solicitacao.despesas[0], solicitacao.periodo
        )

    def test_rn002_intervalo_fechado(self) -> None:
        for data in ("2026-07-01", "2026-07-31"):
            with self.subTest(data=data):
                self.assertIsNone(self._avaliar(data=data))

        decisao = self._avaliar(data="2026-06-30")
        self.assertEqual(decisao.codigo_motivo, "FORA_DA_COMPETENCIA")

    def test_rn003_categoria_case_insensitive(self) -> None:
        self.assertIsNone(self._avaliar(categoria="  ALIMENTACAO  "))

        decisao = self._avaliar(categoria="coworking")
        self.assertEqual(decisao.codigo_motivo, "CATEGORIA_NAO_COBERTA")

    def test_rn004_negativo_contribui_zero(self) -> None:
        decisao = self._avaliar(valor=Decimal("-45.00"))

        self.assertEqual(decisao.codigo_motivo, "VALOR_NAO_POSITIVO")
        self.assertEqual(decisao.valor_reembolsavel, Decimal("0.00"))
        self.assertEqual(decisao.valor_nao_reembolsavel, Decimal("0.00"))

    def test_rn004_zero_e_rejeitado(self) -> None:
        decisao = self._avaliar(valor=Decimal("0"))
        self.assertEqual(decisao.codigo_motivo, "VALOR_NAO_POSITIVO")

    def test_rn011_sem_dado_nao_amplia_limite(self) -> None:
        self.assertEqual(limite_base("alimentacao"), Decimal("60.00"))
        self.assertEqual(limite_base("transporte_urbano"), Decimal("80.00"))
        self.assertEqual(limite_base("hospedagem"), Decimal("250.00"))


if __name__ == "__main__":
    unittest.main()

