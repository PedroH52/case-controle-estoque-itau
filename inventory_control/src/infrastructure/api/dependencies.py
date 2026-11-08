"""
Injeção de Dependências para a aplicação FastAPI.
"""

from __future__ import annotations

from functools import lru_cache

from src.application.use_cases import ServicoEstoque
from src.infrastructure.persistence import RepositorioEstoqueEmMemoria


@lru_cache(maxsize=1)
def _construir_servico() -> ServicoEstoque:
    repositorio = RepositorioEstoqueEmMemoria()
    return ServicoEstoque(repositorio)


def obter_servico_estoque() -> ServicoEstoque:
    """Fornece a instância singleton do serviço de estoque."""
    return _construir_servico()


# Alias
get_inventory_service = obter_servico_estoque
