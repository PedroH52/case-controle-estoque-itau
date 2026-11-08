"""
Exceções de Domínio para o contexto de Controle de Estoque.

Cada exceção mapeia uma violação de regra de negócio específica,
permitindo que as camadas externas (API, CLI, etc.) as traduzam
para os códigos HTTP adequados e mensagens amigáveis em português.
"""


class ExcecaoEstoque(Exception):
    """Classe base para todas as exceções de domínio do estoque."""

    def __init__(self, mensagem: str) -> None:
        super().__init__(mensagem)
        self.mensagem = mensagem

    def __str__(self) -> str:
        return self.mensagem


class QuantidadeInvalidaException(ExcecaoEstoque):
    """Lançada quando o valor de quantidade é menor ou igual a zero."""

    def __init__(self, quantidade: int, motivo: str = "deve ser um número inteiro positivo") -> None:
        super().__init__(f"Quantidade inválida '{quantidade}': {motivo}.")
        self.quantidade = quantidade


class ProdutoDuplicadoException(ExcecaoEstoque):
    """Lançada ao tentar cadastrar um produto cujo identificador (SKU) já existe."""

    def __init__(self, produto_id: str) -> None:
        super().__init__(f"Produto '{produto_id}' já está cadastrado no estoque.")
        self.produto_id = produto_id


class ProdutoNaoEncontradoException(ExcecaoEstoque):
    """Lançada quando a operação referencia um produto inexistente."""

    def __init__(self, produto_id: str) -> None:
        super().__init__(f"Produto '{produto_id}' não foi encontrado no estoque.")
        self.produto_id = produto_id


class EstoqueInsuficienteException(ExcecaoEstoque):
    """Lançada quando a quantidade disponível é inferior à solicitada."""

    def __init__(self, produto_id: str, solicitado: int, disponivel: int) -> None:
        super().__init__(
            f"Estoque disponível insuficiente para o produto '{produto_id}': "
            f"solicitado {solicitado}, disponível {disponivel}."
        )
        self.produto_id = produto_id
        self.solicitado = solicitado
        self.disponivel = disponivel
        self.requested = solicitado
        self.available = disponivel


class ReservaNaoEncontradaException(ExcecaoEstoque):
    """Lançada quando o ID da reserva informada não existe."""

    def __init__(self, reserva_id: str) -> None:
        super().__init__(f"Reserva com identificador '{reserva_id}' não foi encontrada.")
        self.reserva_id = reserva_id
        self.reservation_id = reserva_id


class BloqueioNaoEncontradoException(ExcecaoEstoque):
    """Lançada quando o ID do bloqueio informado não existe."""

    def __init__(self, bloqueio_id: str) -> None:
        super().__init__(f"Bloqueio com identificador '{bloqueio_id}' não foi encontrado.")
        self.bloqueio_id = bloqueio_id
        self.block_id = bloqueio_id


# Aliases para compatibilidade reversa se necessário
InventoryException = ExcecaoEstoque
InvalidQuantityException = QuantidadeInvalidaException
DuplicateProductException = ProdutoDuplicadoException
ProductNotFoundException = ProdutoNaoEncontradoException
InsufficientStockException = EstoqueInsuficienteException
ReservationNotFoundException = ReservaNaoEncontradaException
BlockNotFoundException = BloqueioNaoEncontradoException
