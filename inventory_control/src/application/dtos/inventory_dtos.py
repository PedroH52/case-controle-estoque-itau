"""
Data Transfer Objects (DTOs) da camada de Aplicação.

Responsáveis pela validação e serialização de dados de entrada e saída da API.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# DTOs de Requisição (Entrada de Dados)
# ---------------------------------------------------------------------------

class CriarProdutoRequest(BaseModel):
    produto_id: str = Field(..., min_length=1, description="Identificador único do produto (SKU)")
    nome: str = Field(..., min_length=1, description="Nome do produto")
    quantidade_inicial: int = Field(0, ge=0, description="Quantidade inicial disponível (padrão 0)")


class AdicionarEstoqueRequest(BaseModel):
    quantidade: int = Field(..., gt=0, description="Quantidade de unidades a adicionar ao estoque disponível")


class RemoverEstoqueRequest(BaseModel):
    quantidade: int = Field(..., gt=0, description="Quantidade de unidades a retirar do estoque físico")


class ReservarEstoqueRequest(BaseModel):
    quantidade: int = Field(..., gt=0, description="Quantidade de unidades a reservar")
    motivo: str = Field("", description="Identificação da solicitação, pedido ou referência")


class BloquearEstoqueRequest(BaseModel):
    quantidade: int = Field(..., gt=0, description="Quantidade de unidades a bloquear")
    motivo: str = Field("", description="Justificativa técnica, inspeção de qualidade ou avaria")


# Aliases para compatibilidade reversa
class CreateProductRequest(BaseModel):
    product_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    initial_quantity: int = Field(0, ge=0)


class AddStockRequest(BaseModel):
    quantity: int = Field(..., gt=0)


class RemoveStockRequest(BaseModel):
    quantity: int = Field(..., gt=0)


class ReserveStockRequest(BaseModel):
    quantity: int = Field(..., gt=0)
    label: str = Field("")


class BlockStockRequest(BaseModel):
    quantity: int = Field(..., gt=0)
    label: str = Field("")


# ---------------------------------------------------------------------------
# DTOs de Resposta (Saída de Dados)
# ---------------------------------------------------------------------------

class EntradaEstoqueResponse(BaseModel):
    id: str
    quantidade: int
    motivo: str
    criado_em: datetime


class SituacaoEstoqueResponse(BaseModel):
    produto_id: str
    nome: str
    quantidade_total: int
    quantidade_disponivel: int
    quantidade_reservada: int
    quantidade_bloqueada: int
    reservas: List[EntradaEstoqueResponse] = []
    bloqueios: List[EntradaEstoqueResponse] = []


class OperacaoIdentificadaResponse(BaseModel):
    id: str
    mensagem: str


class MensagemResponse(BaseModel):
    mensagem: str


class ErroResponse(BaseModel):
    erro: str
    detalhe: Optional[str] = None


# Aliases para compatibilidade de testes existentes
StockEntryResponse = EntradaEstoqueResponse
InventorySnapshotResponse = SituacaoEstoqueResponse
ReserveOrBlockResponse = OperacaoIdentificadaResponse
MessageResponse = MensagemResponse
ErrorResponse = ErroResponse
