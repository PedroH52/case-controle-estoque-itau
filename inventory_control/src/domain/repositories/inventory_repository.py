"""
Interface de Repositório (Porta de saída) para persistência de ItemEstoque.

Mantida estritamente na camada de domínio para garantir desacoplamento
total de tecnologias de persistência (SQL, NoSQL, In-Memory).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from src.domain.entities import ItemEstoque


class RepositorioEstoque(ABC):
    """Contrato abstrato de persistência para o agregado ItemEstoque."""

    @abstractmethod
    def buscar_por_id(self, produto_id: str) -> Optional[ItemEstoque]:
        """Retorna o ItemEstoque para o produto_id especificado, ou None se inexistente."""

    @abstractmethod
    def salvar(self, item: ItemEstoque) -> None:
        """Persiste (cria ou atualiza) o ItemEstoque."""

    @abstractmethod
    def existe(self, produto_id: str) -> bool:
        """Retorna True se um produto com o produto_id já existe."""

    @abstractmethod
    def listar_todos(self) -> list[ItemEstoque]:
        """Retorna todos os itens de estoque registrados."""

    # Métodos de compatibilidade em inglês
    def find_by_id(self, product_id: str) -> Optional[ItemEstoque]:
        return self.buscar_por_id(product_id)

    def save(self, item: ItemEstoque) -> None:
        self.salvar(item)

    def exists(self, product_id: str) -> bool:
        return self.existe(product_id)

    def list_all(self) -> list[ItemEstoque]:
        return self.listar_todos()


InventoryRepository = RepositorioEstoque
