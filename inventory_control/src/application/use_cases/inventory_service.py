"""
Casos de Uso da Aplicação para Controle de Estoque.

Orquestra as operações do agregado de domínio e gerencia a persistência.
"""

from __future__ import annotations

from src.domain.entities import ItemEstoque
from src.domain.exceptions import ProdutoDuplicadoException, ProdutoNaoEncontradoException
from src.domain.repositories import RepositorioEstoque


class ServicoEstoque:
    """
    Serviço de aplicação para orquestração de operações de estoque.
    """

    def __init__(self, repositorio: RepositorioEstoque) -> None:
        self._repo = repositorio

    # ------------------------------------------------------------------
    # Cadastro de Produto
    # ------------------------------------------------------------------

    def criar_produto(
        self,
        produto_id: str,
        nome: str,
        quantidade_inicial: int = 0,
    ) -> dict:
        """Cadastra um novo produto no estoque com integridade de SKU."""
        if self._repo.existe(produto_id):
            raise ProdutoDuplicadoException(produto_id)

        item = ItemEstoque(
            produto_id=produto_id,
            nome=nome,
            quantidade_inicial=quantidade_inicial,
        )
        self._repo.salvar(item)
        return item.obter_situacao()

    def create_product(self, product_id: str, name: str, initial_quantity: int = 0) -> dict:
        return self.criar_produto(product_id, name, initial_quantity)

    # ------------------------------------------------------------------
    # Operações de Estoque
    # ------------------------------------------------------------------

    def adicionar_estoque(self, produto_id: str, quantidade: int) -> dict:
        """1. Entrada: Adiciona unidades ao estoque total e disponível."""
        item = self._obter_ou_falhar(produto_id)
        item.adicionar_estoque(quantidade)
        self._repo.salvar(item)
        return item.obter_situacao()

    def add_stock(self, product_id: str, quantity: int) -> dict:
        return self.adicionar_estoque(product_id, quantity)

    def remover_estoque(self, produto_id: str, quantidade: int) -> dict:
        """2. Saída: Retira unidades do estoque disponível."""
        item = self._obter_ou_falhar(produto_id)
        item.remover_estoque(quantidade)
        self._repo.salvar(item)
        return item.obter_situacao()

    def remove_stock(self, product_id: str, quantity: int) -> dict:
        return self.remover_estoque(product_id, quantity)

    def reservar(self, produto_id: str, quantidade: int, motivo: str = "") -> str:
        """3. Reservar: Reserva determinada quantidade para um pedido/solicitação."""
        item = self._obter_ou_falhar(produto_id)
        reserva_id = item.reservar(quantidade, motivo)
        self._repo.salvar(item)
        return reserva_id

    def reserve(self, product_id: str, quantity: int, label: str = "") -> str:
        return self.reservar(product_id, quantity, label)

    def bloquear(self, produto_id: str, quantidade: int, motivo: str = "") -> str:
        """4. Bloquear: Bloqueia determinada quantidade de produto."""
        item = self._obter_ou_falhar(produto_id)
        bloqueio_id = item.bloquear(quantidade, motivo)
        self._repo.salvar(item)
        return bloqueio_id

    def block(self, product_id: str, quantity: int, label: str = "") -> str:
        return self.bloquear(product_id, quantity, label)

    def liberar_reserva(self, produto_id: str, reserva_id: str) -> dict:
        """5. Liberar Reserva: Devolve a quantidade reservada ao disponível."""
        item = self._obter_ou_falhar(produto_id)
        item.liberar_reserva(reserva_id)
        self._repo.salvar(item)
        return item.obter_situacao()

    def release_reservation(self, product_id: str, reservation_id: str) -> dict:
        return self.liberar_reserva(product_id, reservation_id)

    def liberar_bloqueio(self, produto_id: str, bloqueio_id: str) -> dict:
        """5. Liberar Bloqueio: Devolve a quantidade bloqueada ao disponível."""
        item = self._obter_ou_falhar(produto_id)
        item.liberar_bloqueio(bloqueio_id)
        self._repo.salvar(item)
        return item.obter_situacao()

    def release_block(self, product_id: str, block_id: str) -> dict:
        return self.liberar_bloqueio(product_id, block_id)

    # ------------------------------------------------------------------
    # 6. Consultas
    # ------------------------------------------------------------------

    def obter_situacao(self, produto_id: str) -> dict:
        """Consulta o estado atual de determinado produto."""
        return self._obter_ou_falhar(produto_id).obter_situacao()

    def get_snapshot(self, product_id: str) -> dict:
        return self.obter_situacao(product_id)

    def listar_produtos(self) -> list[dict]:
        """Lista a situação de todos os produtos cadastrados."""
        return [item.obter_situacao() for item in self._repo.listar_todos()]

    def list_products(self) -> list[dict]:
        return self.listar_produtos()

    # ------------------------------------------------------------------
    # Auxiliares
    # ------------------------------------------------------------------

    def _obter_ou_falhar(self, produto_id: str) -> ItemEstoque:
        item = self._repo.buscar_por_id(produto_id)
        if item is None:
            raise ProdutoNaoEncontradoException(produto_id)
        return item


InventoryService = ServicoEstoque
