import copy
import unittest
from decimal import Decimal
from pathlib import Path

from src.io_json import EntradaInvalida, carregar_solicitacao, validar_documento


RAIZ = Path(__file__).resolve().parents[1]
EXEMPLO = RAIZ / "exemplos" / "despesas-exemplo.json"


def dados_minimos() -> dict:
    return {
        "colaborador": {"id": "c-1", "nome": "Ana", "centro_custo": "CC-1"},
        "periodo": {
            "competencia": "2026-07",
            "inicio": "2026-07-01",
            "fim": "2026-07-31",
        },
        "despesas": [
            {
                "id": "d-1",
                "data": "2026-07-03",
                "categoria": "alimentacao",
                "descricao": "Almoço",
                "fornecedor": "Restaurante",
                "valor": Decimal("33.333"),
                "tem_nota_fiscal": True,
            }
        ],
    }


class EntradaTests(unittest.TestCase):
    def test_rn001_carrega_exemplo_valido(self) -> None:
        solicitacao = carregar_solicitacao(EXEMPLO)

        self.assertEqual(len(solicitacao.despesas), 14)
        self.assertEqual(solicitacao.despesas[10].valor_original, Decimal("33.333"))
        self.assertEqual(solicitacao.despesas[10].valor_normalizado, Decimal("33.33"))

    def test_rn001_rejeita_id_repetido(self) -> None:
        dados = dados_minimos()
        repetida = copy.deepcopy(dados["despesas"][0])
        dados["despesas"].append(repetida)

        with self.assertRaisesRegex(EntradaInvalida, "identificador repetido"):
            validar_documento(dados)

    def test_rn001_rejeita_periodo_incoerente(self) -> None:
        dados = dados_minimos()
        dados["periodo"]["fim"] = "2026-08-01"

        with self.assertRaisesRegex(EntradaInvalida, "pertencer à competencia"):
            validar_documento(dados)

    def test_rn001_agrega_erros_com_caminhos(self) -> None:
        dados = dados_minimos()
        dados["colaborador"]["nome"] = ""
        dados["despesas"][0]["tem_nota_fiscal"] = "sim"

        with self.assertRaises(EntradaInvalida) as contexto:
            validar_documento(dados)

        mensagem = str(contexto.exception)
        self.assertIn("colaborador.nome", mensagem)
        self.assertIn("despesas[0].tem_nota_fiscal", mensagem)

    def test_rn001_rejeita_json_malformado(self) -> None:
        caminho = RAIZ / "tests" / "fixtures" / "malformado.json"
        with self.assertRaisesRegex(EntradaInvalida, "arquivo"):
            carregar_solicitacao(caminho)


if __name__ == "__main__":
    unittest.main()

