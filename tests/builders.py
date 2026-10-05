from decimal import Decimal

from src.io_json import validar_documento
from src.model import Solicitacao


def criar_solicitacao(*despesas: dict, periodo: dict | None = None) -> Solicitacao:
    periodo_padrao = periodo or {
        "competencia": "2026-07",
        "inicio": "2026-07-01",
        "fim": "2026-07-31",
    }
    itens = []
    for indice, alteracoes in enumerate(despesas, start=1):
        item = {
            "id": f"d-{indice}",
            "data": "2026-07-03",
            "categoria": "alimentacao",
            "descricao": f"Despesa {indice}",
            "fornecedor": "Fornecedor",
            "valor": Decimal("10.00"),
            "tem_nota_fiscal": True,
        }
        item.update(alteracoes)
        itens.append(item)
    return validar_documento(
        {
            "colaborador": {
                "id": "c-1",
                "nome": "Ana",
                "centro_custo": "CC-1",
            },
            "periodo": periodo_padrao,
            "despesas": itens,
        }
    )

