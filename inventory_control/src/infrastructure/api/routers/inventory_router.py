"""
Roteador FastAPI – Endpoints de Controle de Estoque (100% em Português).

Rotas:
  POST   /produtos                                      -> Cadastrar novo produto
  GET    /produtos                                      -> Listar todos os produtos
  GET    /produtos/{produto_id}                         -> Consultar situação do estoque
  POST   /produtos/{produto_id}/estoque/entrada         -> 1. Entrada de estoque
  POST   /produtos/{produto_id}/estoque/saida           -> 2. Saída de estoque
  POST   /produtos/{produto_id}/reservas                -> 3. Reservar unidades
  DELETE /produtos/{produto_id}/reservas/{reserva_id}   -> 5. Liberar reserva
  POST   /produtos/{produto_id}/bloqueios               -> 4. Bloquear unidades
  DELETE /produtos/{produto_id}/bloqueios/{bloqueio_id} -> 5. Liberar bloqueio
"""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, status

from src.application.dtos import (
    AdicionarEstoqueRequest,
    BloquearEstoqueRequest,
    CriarProdutoRequest,
    OperacaoIdentificadaResponse,
    RemoverEstoqueRequest,
    ReservarEstoqueRequest,
    SituacaoEstoqueResponse,
)
from src.application.use_cases import ServicoEstoque
from src.infrastructure.api.dependencies import obter_servico_estoque

router = APIRouter(prefix="/produtos", tags=["Controle de Estoque"])


@router.post(
    "",
    response_model=SituacaoEstoqueResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar um novo produto",
    description="Registra um novo produto no catálogo do estoque com quantidade inicial opcional.",
)
def cadastrar_produto(
    corpo: CriarProdutoRequest,
    servico: ServicoEstoque = Depends(obter_servico_estoque),
) -> SituacaoEstoqueResponse:
    situacao = servico.criar_produto(
        produto_id=corpo.produto_id,
        nome=corpo.nome,
        quantidade_inicial=corpo.quantidade_inicial,
    )
    return SituacaoEstoqueResponse(**situacao)


@router.get(
    "",
    response_model=List[SituacaoEstoqueResponse],
    summary="Listar todos os produtos",
    description="Retorna a situação completa e o estado das quantidades de todos os produtos.",
)
def listar_produtos(
    servico: ServicoEstoque = Depends(obter_servico_estoque),
) -> List[SituacaoEstoqueResponse]:
    return [SituacaoEstoqueResponse(**s) for s in servico.listar_produtos()]


@router.get(
    "/{produto_id}",
    response_model=SituacaoEstoqueResponse,
    summary="6. Consultar situação atual do produto",
    description="Retorna a quantidade total, disponível, reservada, bloqueada e as listas de reservas e bloqueios ativos.",
)
def consultar_produto(
    produto_id: str,
    servico: ServicoEstoque = Depends(obter_servico_estoque),
) -> SituacaoEstoqueResponse:
    return SituacaoEstoqueResponse(**servico.obter_situacao(produto_id))


@router.post(
    "/{produto_id}/estoque/entrada",
    response_model=SituacaoEstoqueResponse,
    summary="1. Entrada de estoque",
    description="Adiciona uma determinada quantidade de unidades ao estoque disponível e total do produto.",
)
def entrada_estoque(
    produto_id: str,
    corpo: AdicionarEstoqueRequest,
    servico: ServicoEstoque = Depends(obter_servico_estoque),
) -> SituacaoEstoqueResponse:
    return SituacaoEstoqueResponse(**servico.adicionar_estoque(produto_id, corpo.quantidade))


@router.post(
    "/{produto_id}/estoque/saida",
    response_model=SituacaoEstoqueResponse,
    summary="2. Saída de estoque",
    description="Retira unidades do estoque físico. Permitido apenas se houver quantidade disponível suficiente.",
)
def saida_estoque(
    produto_id: str,
    corpo: RemoverEstoqueRequest,
    servico: ServicoEstoque = Depends(obter_servico_estoque),
) -> SituacaoEstoqueResponse:
    return SituacaoEstoqueResponse(**servico.remover_estoque(produto_id, corpo.quantidade))


@router.post(
    "/{produto_id}/reservas",
    response_model=OperacaoIdentificadaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="3. Reservar unidades do estoque",
    description="Reserva unidades disponíveis para uma solicitação ou pedido. Gera um identificador único de reserva.",
)
def reservar_estoque(
    produto_id: str,
    corpo: ReservarEstoqueRequest,
    servico: ServicoEstoque = Depends(obter_servico_estoque),
) -> OperacaoIdentificadaResponse:
    reserva_id = servico.reservar(produto_id, corpo.quantidade, corpo.motivo)
    return OperacaoIdentificadaResponse(
        id=reserva_id,
        mensagem=f"Reserva de {corpo.quantidade} unidade(s) criada com sucesso. Identificador: {reserva_id}",
    )


@router.delete(
    "/{produto_id}/reservas/{reserva_id}",
    response_model=SituacaoEstoqueResponse,
    summary="5. Liberar reserva existente",
    description="Libera a reserva informada pelo ID, devolvendo a quantidade exata para o estoque disponível.",
)
def liberar_reserva(
    produto_id: str,
    reserva_id: str,
    servico: ServicoEstoque = Depends(obter_servico_estoque),
) -> SituacaoEstoqueResponse:
    return SituacaoEstoqueResponse(**servico.liberar_reserva(produto_id, reserva_id))


@router.post(
    "/{produto_id}/bloqueios",
    response_model=OperacaoIdentificadaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="4. Bloquear unidades do estoque",
    description="Bloqueia unidades tornando-as indisponíveis para utilização. Gera um identificador único de bloqueio.",
)
def bloquear_estoque(
    produto_id: str,
    corpo: BloquearEstoqueRequest,
    servico: ServicoEstoque = Depends(obter_servico_estoque),
) -> OperacaoIdentificadaResponse:
    bloqueio_id = servico.bloquear(produto_id, corpo.quantidade, corpo.motivo)
    return OperacaoIdentificadaResponse(
        id=bloqueio_id,
        mensagem=f"Bloqueio de {corpo.quantidade} unidade(s) realizado com sucesso. Identificador: {bloqueio_id}",
    )


@router.delete(
    "/{produto_id}/bloqueios/{bloqueio_id}",
    response_model=SituacaoEstoqueResponse,
    summary="5. Liberar bloqueio existente",
    description="Libera o bloqueio informado pelo ID, devolvendo a quantidade exata para o estoque disponível.",
)
def liberar_bloqueio(
    produto_id: str,
    bloqueio_id: str,
    servico: ServicoEstoque = Depends(obter_servico_estoque),
) -> SituacaoEstoqueResponse:
    return SituacaoEstoqueResponse(**servico.liberar_bloqueio(produto_id, bloqueio_id))


# Aliases para compatibilidade reversa com chamadas em inglês
create_product = cadastrar_produto
list_products = listar_produtos
get_product = consultar_produto
add_stock = entrada_estoque
remove_stock = saida_estoque
reserve_stock = reservar_estoque
release_reservation = liberar_reserva
block_stock = bloquear_estoque
release_block = liberar_bloqueio
