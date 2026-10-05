import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path

from src.cli import main


RAIZ = Path(__file__).resolve().parents[1]
EXEMPLO = RAIZ / "exemplos" / "despesas-exemplo.json"
MALFORMADO = RAIZ / "tests" / "fixtures" / "malformado.json"


class CliTests(unittest.TestCase):
    def test_cli_calcular_cria_saida(self) -> None:
        with tempfile.TemporaryDirectory() as pasta:
            destino = Path(pasta) / "resultado.json"
            with redirect_stdout(StringIO()):
                codigo = main(
                    [
                        "calcular",
                        "--input",
                        str(EXEMPLO),
                        "--output",
                        str(destino),
                    ]
                )

            self.assertEqual(codigo, 0)
            resultado = json.loads(destino.read_text(encoding="utf-8"))
            self.assertEqual(resultado["resumo"]["total_reembolsavel"], "585.43")

    def test_cli_entrada_invalida_preserva_destino(self) -> None:
        with tempfile.TemporaryDirectory() as pasta:
            destino = Path(pasta) / "resultado.json"
            destino.write_text("conteúdo anterior", encoding="utf-8")

            with redirect_stderr(StringIO()):
                codigo = main(
                    [
                        "calcular",
                        "--input",
                        str(MALFORMADO),
                        "--output",
                        str(destino),
                    ]
                )

            self.assertEqual(codigo, 2)
            self.assertEqual(
                destino.read_text(encoding="utf-8"), "conteúdo anterior"
            )

    def test_cli_falha_operacional_retorna_um(self) -> None:
        destino = RAIZ / "diretorio-inexistente" / "resultado.json"
        with redirect_stderr(StringIO()):
            codigo = main(
                ["calcular", "--input", str(EXEMPLO), "--output", str(destino)]
            )
        self.assertEqual(codigo, 1)


if __name__ == "__main__":
    unittest.main()

