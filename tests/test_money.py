import unittest
from decimal import Decimal

from src.money import formatar_original, formatar_valor, normalizar_valor


class MoneyTests(unittest.TestCase):
    def test_rn012_arredonda_meio_para_longe_de_zero(self) -> None:
        casos = {
            "33.333": "33.33",
            "33.335": "33.34",
            "-33.335": "-33.34",
            "100.005": "100.01",
        }

        for recebido, esperado in casos.items():
            with self.subTest(recebido=recebido):
                self.assertEqual(
                    normalizar_valor(Decimal(recebido)), Decimal(esperado)
                )

    def test_rn012_formata_duas_casas(self) -> None:
        self.assertEqual(formatar_valor(Decimal("2")), "2.00")
        self.assertEqual(formatar_valor(Decimal("33.333")), "33.33")

    def test_valor_original_nao_e_arredondado(self) -> None:
        self.assertEqual(formatar_original(Decimal("33.333")), "33.333")


if __name__ == "__main__":
    unittest.main()

