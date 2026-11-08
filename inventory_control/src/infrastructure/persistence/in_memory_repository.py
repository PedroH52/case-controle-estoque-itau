"""
Implementação em memória do RepositorioEstoque.

Características:
- Armazenamento em dicionário nativo (O(1) para buscas por produto_id).
- Thread-safe com trava reentrante (threading.RLock) no nível do repositório.
"""

from __future__ import annotations

import threading
from typing import Optional

from src.domain.entities import ItemEstoque
from src.domain.repositories import RepositorioEstoque


class RepositorioEstoqueEmMemoria(RepositorioEstoque):
    """Repositório thread-safe em memória."""

    def __init__(self) -> None:
        self._dados: dict[str, ItemEstoque] = {}
        self._lock = threading.RLock()

    def buscar_por_id(self, produto_id: str) -> Optional[ItemEstoque]:
        with self._lock:
            return self._dados.get(produto_id)

    def salvar(self, item: ItemEstoque) -> None:
        with self._lock:
            self._dados[item.produto_id] = item

    def existe(self, produto_id: str) -> bool:
        with self._lock:
            return produto_id in self._dados

    def listar_todos(self) -> list[ItemEstoque]:
        with self._lock:
            return list(self._dados.values())


InMemoryInventoryRepository = RepositorioEstoqueEmMemoria
