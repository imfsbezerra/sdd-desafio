import unittest
from decimal import Decimal
from pathlib import Path

from src.config import carregar_cambio, carregar_politica
from src.engine import processar_solicitacao_v4
from tests.builders import criar_solicitacao


RAIZ = Path(__file__).resolve().parents[1]
ENVELOPE = RAIZ / "exemplos" / "envelope"
POLITICA = carregar_politica(ENVELOPE / "politica-v4.json")
CAMBIO = carregar_cambio(ENVELOPE / "cambio.json")


class ResultadoV4Tests(unittest.TestCase):
    def test_rn016_saida_v4_preserva_ordem_e_reconcilia(self) -> None:
        solicitacao = criar_solicitacao(
            {"id": "primeira", "valor": Decimal("40")},
            {"id": "segunda", "valor": Decimal("40")},
        )

        resultado = processar_solicitacao_v4(solicitacao, POLITICA, CAMBIO)
        resumo = resultado["resumo"]

        self.assertEqual(resultado["politica"]["versao"], "v4")
        self.assertEqual(resultado["politica"]["origem_limites"], "padrao")
        self.assertEqual(
            [item["id"] for item in resultado["decisoes"]],
            ["primeira", "segunda"],
        )
        self.assertEqual(resumo["total_solicitado"], "80.00")
        self.assertEqual(resumo["total_reembolsavel"], "60.00")
        self.assertEqual(resumo["total_nao_reembolsavel"], "20.00")

    def test_rn008_sem_cotacao_incrementa_contagem(self) -> None:
        solicitacao = criar_solicitacao(
            {
                "categoria": "alimentacao",
                "moeda": "GBP",
                "valor": Decimal("55"),
                "data": "2026-07-21",
            }
        )

        resultado = processar_solicitacao_v4(solicitacao, POLITICA, CAMBIO)
        decisao = resultado["decisoes"][0]

        self.assertEqual(decisao["codigo_motivo"], "COTACAO_INDISPONIVEL")
        self.assertIsNone(decisao["taxa_cambio"])
        self.assertIsNone(decisao["valor_convertido_brl"])
        self.assertEqual(resultado["resumo"]["quantidade_sem_conversao"], 1)
        self.assertEqual(resultado["resumo"]["total_solicitado"], "0.00")

    def test_saida_v4_registra_taxa_e_data(self) -> None:
        solicitacao = criar_solicitacao(
            {
                "categoria": "alimentacao",
                "moeda": "EUR",
                "valor": Decimal("22"),
                "data": "2026-07-14",
            }
        )

        decisao = processar_solicitacao_v4(solicitacao, POLITICA, CAMBIO)[
            "decisoes"
        ][0]

        self.assertEqual(decisao["taxa_cambio"], "5.930000")
        self.assertEqual(decisao["data_taxa_cambio"], "2026-07-14")
        self.assertEqual(decisao["valor_convertido_brl"], "130.46")


if __name__ == "__main__":
    unittest.main()
