import unittest
from decimal import Decimal
from pathlib import Path

from src.engine import processar_solicitacao
from src.io_json import carregar_solicitacao
from tests.builders import criar_solicitacao


RAIZ = Path(__file__).resolve().parents[1]


class ResultadoTests(unittest.TestCase):
    def test_rn013_preserva_ordem_e_reconcilia_totais(self) -> None:
        solicitacao = criar_solicitacao(
            {"id": "primeira", "valor": Decimal("40.00")},
            {"id": "segunda", "valor": Decimal("40.00")},
            {"id": "terceira", "valor": Decimal("-10.00")},
        )

        resultado = processar_solicitacao(solicitacao)
        resumo = resultado["resumo"]

        self.assertEqual(
            [item["id"] for item in resultado["decisoes"]],
            ["primeira", "segunda", "terceira"],
        )
        self.assertEqual(resumo["total_solicitado"], "80.00")
        self.assertEqual(resumo["total_reembolsavel"], "60.00")
        self.assertEqual(resumo["total_nao_reembolsavel"], "20.00")
        self.assertEqual(
            resumo["quantidade_aprovadas"]
            + resumo["quantidade_parciais"]
            + resumo["quantidade_rejeitadas"],
            resumo["quantidade_despesas"],
        )

    def test_saida_obedece_schema_da_spec(self) -> None:
        resultado = processar_solicitacao(criar_solicitacao({}))

        self.assertEqual(
            set(resultado),
            {"politica_versao", "colaborador", "periodo", "resumo", "decisoes"},
        )
        self.assertEqual(
            set(resultado["decisoes"][0]),
            {
                "id",
                "status",
                "valor_original",
                "valor_normalizado",
                "valor_reembolsavel",
                "valor_nao_reembolsavel",
                "codigo_motivo",
                "justificativa",
                "regras_aplicadas",
            },
        )

    def test_exemplo_tem_totais_derivados_da_spec(self) -> None:
        solicitacao = carregar_solicitacao(
            RAIZ / "exemplos" / "despesas-exemplo.json"
        )

        resultado = processar_solicitacao(solicitacao)

        self.assertEqual(len(resultado["decisoes"]), 14)
        self.assertEqual(resultado["resumo"]["total_solicitado"], "1861.84")
        self.assertEqual(resultado["resumo"]["total_reembolsavel"], "585.43")
        self.assertEqual(resultado["resumo"]["total_nao_reembolsavel"], "1276.41")
        self.assertEqual(resultado["resumo"]["quantidade_aprovadas"], 3)
        self.assertEqual(resultado["resumo"]["quantidade_parciais"], 4)
        self.assertEqual(resultado["resumo"]["quantidade_rejeitadas"], 7)


if __name__ == "__main__":
    unittest.main()

