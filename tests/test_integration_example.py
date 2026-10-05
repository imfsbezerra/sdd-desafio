import unittest
from pathlib import Path

from src.engine import processar_solicitacao
from src.io_json import carregar_solicitacao


RAIZ = Path(__file__).resolve().parents[1]
EXEMPLO = RAIZ / "exemplos" / "despesas-exemplo.json"


class IntegracaoExemploTests(unittest.TestCase):
    def test_integracao_exemplo_gera_14_decisoes_e_totais_exatos(self) -> None:
        resultado = processar_solicitacao(carregar_solicitacao(EXEMPLO))

        esperado = [
            ("d-001", "PARCIAL", "LIMITE_PARCIAL", "60.00"),
            ("d-002", "REJEITADA", "LIMITE_ESGOTADO", "0.00"),
            ("d-003", "PARCIAL", "LIMITE_PARCIAL", "80.00"),
            ("d-004", "REJEITADA", "NOTA_FISCAL_AUSENTE", "0.00"),
            ("d-005", "REJEITADA", "CATEGORIA_NAO_COBERTA", "0.00"),
            ("d-006", "APROVADA", "APROVADA_INTEGRAL", "54.90"),
            ("d-007", "REJEITADA", "DUPLICATA", "0.00"),
            ("d-008", "REJEITADA", "FORA_DA_COMPETENCIA", "0.00"),
            ("d-009", "REJEITADA", "VALOR_NAO_POSITIVO", "0.00"),
            ("d-010", "PARCIAL", "LIMITE_PARCIAL", "250.00"),
            ("d-011", "APROVADA", "APROVADA_INTEGRAL", "33.33"),
            ("d-012", "APROVADA", "APROVADA_INTEGRAL", "47.20"),
            ("d-013", "REJEITADA", "NOTA_FISCAL_AUSENTE", "0.00"),
            ("d-014", "PARCIAL", "LIMITE_PARCIAL", "60.00"),
        ]
        obtido = [
            (
                item["id"],
                item["status"],
                item["codigo_motivo"],
                item["valor_reembolsavel"],
            )
            for item in resultado["decisoes"]
        ]

        self.assertEqual(obtido, esperado)
        self.assertEqual(
            resultado["resumo"],
            {
                "quantidade_despesas": 14,
                "total_solicitado": "1861.84",
                "total_reembolsavel": "585.43",
                "total_nao_reembolsavel": "1276.41",
                "quantidade_aprovadas": 3,
                "quantidade_parciais": 4,
                "quantidade_rejeitadas": 7,
            },
        )


if __name__ == "__main__":
    unittest.main()

