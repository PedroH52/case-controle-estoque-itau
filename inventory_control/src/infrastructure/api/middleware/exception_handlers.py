"""
Middleware de tratamento global de exceções.

Mapeia as exceções de domínio para códigos HTTP expressivos e mensagens em português.
"""

from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse

from src.domain.exceptions import (
    BloqueioNaoEncontradoException,
    EstoqueInsuficienteException,
    ExcecaoEstoque,
    ProdutoDuplicadoException,
    ProdutoNaoEncontradoException,
    QuantidadeInvalidaException,
    ReservaNaoEncontradaException,
)


def manipulador_excecoes_estoque(request: Request | None, exc: ExcecaoEstoque) -> JSONResponse:
    mapa_status: dict[type, int] = {
        ProdutoNaoEncontradoException: 404,
        ProdutoDuplicadoException: 409,
        EstoqueInsuficienteException: 422,
        ReservaNaoEncontradaException: 404,
        BloqueioNaoEncontradoException: 404,
        QuantidadeInvalidaException: 400,
    }
    status_code = mapa_status.get(type(exc), 400)
    return JSONResponse(
        status_code=status_code,
        content={"erro": type(exc).__name__, "detalhe": exc.mensagem},
    )


def manipulador_excecao_generica(request: Request | None, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"erro": "ErroInternoDoServidor", "detalhe": "Ocorreu um erro interno inesperado."},
    )


# Aliases
inventory_exception_handler = manipulador_excecoes_estoque
generic_exception_handler = manipulador_excecao_generica
