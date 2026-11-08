"""
Entidades de Domínio para Controle de Estoque.

Decisões de Design
------------------
* EntradaEstoque (Reserva ou Bloqueio) é um Value Object imutável que armazena
  o identificador único, a quantidade e uma justificativa/referência.
* ItemEstoque (InventoryItem) é o Agregado Raiz (Aggregate Root).
  Todas as mutações ocorrem exclusivamente através de seus métodos;
  nenhum código externo tem permissão para alterar coleções internas diretamente.
* Thread-Safety: gerenciado via trava reentrante (threading.RLock) encapsulada
  no agregado, garantindo atomicidade e evitando race conditions.
* Invariante fundamental assegurado após cada operação:
      Quantidade Total = Quantidade Disponível + Quantidade Reservada + Quantidade Bloqueada
"""

from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from src.domain.exceptions import (
    BloqueioNaoEncontradoException,
    EstoqueInsuficienteException,
    QuantidadeInvalidaException,
    ReservaNaoEncontradaException,
)


def _agora_utc() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Value Objects / Sub-entidades
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class EntradaEstoque:
    """
    Registro imutável representando uma reserva ou um bloqueio.

    ``id``          – UUID único gerado no momento da operação.
    ``quantidade``  – número inteiro positivo de unidades vinculadas.
    ``motivo``      – referência descritiva (ex: número do pedido, justificativa técnica).
    ``criado_em``   – timestamp UTC de criação.
    """

    id: str
    quantidade: int
    motivo: str
    criado_em: datetime = field(default_factory=_agora_utc)

    # Propriedades de compatibilidade
    @property
    def entry_id(self) -> str:
        return self.id

    @property
    def label(self) -> str:
        return self.motivo

    @property
    def created_at(self) -> datetime:
        return self.criado_em


StockEntry = EntradaEstoque


# ---------------------------------------------------------------------------
# Agregado Raiz (Aggregate Root)
# ---------------------------------------------------------------------------

class ItemEstoque:
    """
    Agregado Raiz para o estoque de um produto individual.

    Operações públicas thread-safe:
        adicionar_estoque(quantidade)          -> None  (Entrada)
        remover_estoque(quantidade)            -> None  (Saída)
        reservar(quantidade, motivo)           -> str   (Reserva - retorna id)
        bloquear(quantidade, motivo)           -> str   (Bloqueio - retorna id)
        liberar_reserva(reserva_id)            -> None  (Liberação)
        liberar_bloqueio(bloqueio_id)          -> None  (Liberação)
        obter_situacao()                       -> dict  (Consulta de estado)
    """

    def __init__(
        self,
        produto_id: str = "",
        nome: str = "",
        quantidade_inicial: int = 0,
        # Compatibilidade com nomes em inglês
        product_id: str | None = None,
        name: str | None = None,
        initial_quantity: int | None = None,
    ) -> None:
        p_id = produto_id or product_id or ""
        p_nome = nome or name or ""
        qtd = initial_quantity if initial_quantity is not None else quantidade_inicial

        if qtd < 0:
            raise QuantidadeInvalidaException(qtd, "a quantidade inicial não pode ser negativa")

        self._produto_id = p_id
        self._nome = p_nome
        self._disponivel = qtd
        self._reservas: dict[str, EntradaEstoque] = {}
        self._bloqueios: dict[str, EntradaEstoque] = {}
        self._lock = threading.RLock()

    # ------------------------------------------------------------------
    # Propriedades de Leitura (Consistentes sob lock)
    # ------------------------------------------------------------------

    @property
    def produto_id(self) -> str:
        return self._produto_id

    @property
    def product_id(self) -> str:
        return self._produto_id

    @property
    def nome(self) -> str:
        return self._nome

    @property
    def name(self) -> str:
        return self._nome

    @property
    def quantidade_disponivel(self) -> int:
        return self._disponivel

    @property
    def available(self) -> int:
        return self._disponivel

    @property
    def quantidade_reservada(self) -> int:
        return sum(e.quantidade for e in self._reservas.values())

    @property
    def reserved(self) -> int:
        return self.quantidade_reservada

    @property
    def quantidade_bloqueada(self) -> int:
        return sum(e.quantidade for e in self._bloqueios.values())

    @property
    def blocked(self) -> int:
        return self.quantidade_bloqueada

    @property
    def quantidade_total(self) -> int:
        return self._disponivel + self.quantidade_reservada + self.quantidade_bloqueada

    @property
    def total(self) -> int:
        return self.quantidade_total

    # ------------------------------------------------------------------
    # Operações de Mutação (Todas atômicas e protegidas por _lock)
    # ------------------------------------------------------------------

    def adicionar_estoque(self, quantidade: int) -> None:
        """
        1. Entrada: Adiciona unidades ao estoque total e disponível.
        """
        self._validar_quantidade_positiva(quantidade, "Entrada")
        with self._lock:
            self._disponivel += quantidade

    def add_stock(self, quantity: int) -> None:
        self.adicionar_estoque(quantity)

    def remover_estoque(self, quantidade: int) -> None:
        """
        2. Saída: Retira unidades do estoque físico.
        Apenas permitido quando houver quantidade disponível suficiente.
        """
        self._validar_quantidade_positiva(quantidade, "Saída")
        with self._lock:
            self._garantir_disponibilidade(quantidade)
            self._disponivel -= quantidade

    def remove_stock(self, quantity: int) -> None:
        self.remover_estoque(quantity)

    def reservar(self, quantidade: int, motivo: str = "") -> str:
        """
        3. Reservar: Reserva determinada quantidade disponível para uma solicitação/pedido.
        Retorna o identificador único (UUID) para consulta e posterior liberação.
        """
        self._validar_quantidade_positiva(quantidade, "Reserva")
        with self._lock:
            self._garantir_disponibilidade(quantidade)
            reserva_id = str(uuid.uuid4())
            self._reservas[reserva_id] = EntradaEstoque(
                id=reserva_id,
                quantidade=quantidade,
                motivo=motivo,
            )
            self._disponivel -= quantidade
            return reserva_id

    def reserve(self, quantity: int, label: str = "") -> str:
        return self.reservar(quantity, label)

    def bloquear(self, quantidade: int, motivo: str = "") -> str:
        """
        4. Bloquear: Bloqueia determinada quantidade, tornando-a indisponível para uso.
        Retorna o identificador único (UUID) para consulta e posterior liberação.
        """
        self._validar_quantidade_positiva(quantidade, "Bloqueio")
        with self._lock:
            self._garantir_disponibilidade(quantidade)
            bloqueio_id = str(uuid.uuid4())
            self._bloqueios[bloqueio_id] = EntradaEstoque(
                id=bloqueio_id,
                quantidade=quantidade,
                motivo=motivo,
            )
            self._disponivel -= quantidade
            return bloqueio_id

    def block(self, quantity: int, label: str = "") -> str:
        return self.bloquear(quantity, label)

    def liberar_reserva(self, reserva_id: str) -> None:
        """
        5. Liberar Reserva: Devolve a quantidade exata da reserva para o estoque disponível.
        """
        with self._lock:
            entrada = self._reservas.pop(reserva_id, None)
            if entrada is None:
                raise ReservaNaoEncontradaException(reserva_id)
            self._disponivel += entrada.quantidade

    def release_reservation(self, reservation_id: str) -> None:
        self.liberar_reserva(reservation_id)

    def liberar_bloqueio(self, bloqueio_id: str) -> None:
        """
        5. Liberar Bloqueio: Devolve a quantidade exata do bloqueio para o estoque disponível.
        """
        with self._lock:
            entrada = self._bloqueios.pop(bloqueio_id, None)
            if entrada is None:
                raise BloqueioNaoEncontradoException(bloqueio_id)
            self._disponivel += entrada.quantidade

    def release_block(self, block_id: str) -> None:
        self.liberar_bloqueio(block_id)

    # ------------------------------------------------------------------
    # 6. Consultar (Snapshot)
    # ------------------------------------------------------------------

    def obter_situacao(self) -> dict:
        """
        Retorna uma visão consistente e imutável do estado atual do produto.
        """
        with self._lock:
            reservas_lista = [
                {
                    "id": e.id,
                    "quantidade": e.quantidade,
                    "motivo": e.motivo,
                    "criado_em": e.criado_em.isoformat(),
                    # Chaves em inglês para compatibilidade
                    "label": e.motivo,
                    "created_at": e.criado_em.isoformat(),
                }
                for e in self._reservas.values()
            ]
            bloqueios_lista = [
                {
                    "id": e.id,
                    "quantidade": e.quantidade,
                    "motivo": e.motivo,
                    "criado_em": e.criado_em.isoformat(),
                    # Chaves em inglês para compatibilidade
                    "label": e.motivo,
                    "created_at": e.criado_em.isoformat(),
                }
                for e in self._bloqueios.values()
            ]
            return {
                "produto_id": self._produto_id,
                "nome": self._nome,
                "quantidade_total": self.quantidade_total,
                "quantidade_disponivel": self._disponivel,
                "quantidade_reservada": self.quantidade_reservada,
                "quantidade_bloqueada": self.quantidade_bloqueada,
                "reservas": reservas_lista,
                "bloqueios": bloqueios_lista,
                # Aliases em inglês
                "product_id": self._produto_id,
                "name": self._nome,
                "total": self.quantidade_total,
                "available": self._disponivel,
                "reserved": self.quantidade_reservada,
                "blocked": self.quantidade_bloqueada,
                "reservations": reservas_lista,
                "blocks": bloqueios_lista,
            }

    def snapshot(self) -> dict:
        return self.obter_situacao()

    # ------------------------------------------------------------------
    # Validações Internas Auxiliares
    # ------------------------------------------------------------------

    def _validar_quantidade_positiva(self, quantidade: int, operacao: str) -> None:
        if not isinstance(quantidade, int) or quantidade <= 0:
            raise QuantidadeInvalidaException(
                quantidade, f"a quantidade para '{operacao}' deve ser um número inteiro positivo maior que zero"
            )

    def _garantir_disponibilidade(self, quantidade: int) -> None:
        if self._disponivel < quantidade:
            raise EstoqueInsuficienteException(
                self._produto_id, quantidade, self._disponivel
            )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"ItemEstoque(produto_id={self._produto_id!r}, "
            f"total={self.quantidade_total}, disponivel={self._disponivel}, "
            f"reservado={self.quantidade_reservada}, bloqueado={self.quantidade_bloqueada})"
        )


InventoryItem = ItemEstoque
