import unittest
from decimal import Decimal
from pathlib import Path

from src.config import carregar_politica
from src.engine import (
    aplicar_limite_v4,
    assinatura_duplicidade_v4,
    avaliar_politica_e_documentos_v4,
    selecionar_tabela,
)
from src.model import Conversao, RegraCategoria, Status
from tests.builders import criar_solicitacao


RAIZ = Path(__file__).resolve().parents[1]
POLITICA = carregar_politica(RAIZ / "exemplos" / "envelope" / "politica-v4.json")


def conversao(despesa, valor_brl: str) -> Conversao:
    return Conversao(
        despesa.moeda,
        Decimal("1") if despesa.moeda == "BRL" else Decimal("5.50"),
        despesa.data,
        Decimal(valor_brl),
    )


class PolicyV4Tests(unittest.TestCase):
    def test_rn003_centro_desconhecido_usa_padrao(self) -> None:
        origem, tabela = selecionar_tabela(POLITICA, "CC-SUPORTE-N2")

        self.assertEqual(origem, "padrao")
        self.assertEqual(tabela["alimentacao"].limite, Decimal("60.00"))
        self.assertNotIn("representacao", tabela)

    def test_amb016_centro_conhecido_nao_mescla_padrao(self) -> None:
        origem, tabela = selecionar_tabela(POLITICA, "CC-ADM")

        self.assertEqual(origem, "centro_custo")
        self.assertNotIn("hospedagem", tabela)

    def test_rn004_categoria_zero_e_rejeitada(self) -> None:
        despesa = criar_solicitacao(
            {"categoria": "hospedagem", "valor": Decimal("200")}
        ).despesas[0]
        _, tabela = selecionar_tabela(POLITICA, "CC-ENG-PLATAFORMA")

        decisao, regra = avaliar_politica_e_documentos_v4(
            despesa, conversao(despesa, "200"), tabela, POLITICA, set()
        )

        self.assertIsNone(regra)
        self.assertEqual(decisao.codigo_motivo, "CATEGORIA_NAO_REEMBOLSAVEL")

    def test_rn004_representacao_e_dinamica(self) -> None:
        despesa = criar_solicitacao(
            {"categoria": "representacao", "valor": Decimal("340")}
        ).despesas[0]
        _, tabela = selecionar_tabela(POLITICA, "CC-COMERCIAL")

        decisao, regra = avaliar_politica_e_documentos_v4(
            despesa, conversao(despesa, "340"), tabela, POLITICA, set()
        )
        final = aplicar_limite_v4(despesa, conversao(despesa, "340"), regra, {})

        self.assertIsNone(decisao)
        self.assertEqual(final.status, Status.PARCIAL)
        self.assertEqual(final.valor_reembolsavel, Decimal("300.00"))

    def test_rn010_nota_usa_valor_brl(self) -> None:
        despesa = criar_solicitacao(
            {
                "categoria": "transporte_urbano",
                "moeda": "USD",
                "valor": Decimal("40"),
                "tem_nota_fiscal": False,
            }
        ).despesas[0]
        _, tabela = selecionar_tabela(POLITICA, "CC-COMERCIAL")

        decisao, _ = avaliar_politica_e_documentos_v4(
            despesa, conversao(despesa, "220"), tabela, POLITICA, set()
        )

        self.assertEqual(decisao.codigo_motivo, "NOTA_FISCAL_AUSENTE")

    def test_rn011_assinatura_inclui_moeda(self) -> None:
        solicitacao = criar_solicitacao(
            {"descricao": "Táxi", "moeda": "USD", "valor": Decimal("10")},
            {"descricao": "Táxi", "moeda": "EUR", "valor": Decimal("10")},
        )

        self.assertNotEqual(
            assinatura_duplicidade_v4(solicitacao.despesas[0]),
            assinatura_duplicidade_v4(solicitacao.despesas[1]),
        )

    def test_rn012_periodicidade_dinamica(self) -> None:
        solicitacao = criar_solicitacao(
            {"valor": Decimal("40"), "descricao": "A"},
            {"valor": Decimal("40"), "descricao": "B"},
        )
        regra_dia = RegraCategoria(Decimal("60"), "dia")
        saldos = {}

        primeira = aplicar_limite_v4(
            solicitacao.despesas[0], conversao(solicitacao.despesas[0], "40"), regra_dia, saldos
        )
        segunda = aplicar_limite_v4(
            solicitacao.despesas[1], conversao(solicitacao.despesas[1], "40"), regra_dia, saldos
        )

        self.assertEqual(primeira.valor_reembolsavel, Decimal("40"))
        self.assertEqual(segunda.valor_reembolsavel, Decimal("20"))

    def test_rn014_percentual_nao_altera_limite_sem_indicador(self) -> None:
        _, tabela = selecionar_tabela(POLITICA, "CC-COMERCIAL")
        self.assertEqual(POLITICA.acrescimo_viagem_percentual, Decimal("50"))
        self.assertEqual(tabela["alimentacao"].limite, Decimal("90.00"))


if __name__ == "__main__":
    unittest.main()
