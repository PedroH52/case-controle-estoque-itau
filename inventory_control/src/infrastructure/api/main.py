"""
Ponto de entrada da API FastAPI (Controle de Estoque).

Configura:
- Roteadores da API
- Manipulador global de exceções de domínio e erros genéricos
- Endpoints de monitoramento (/saude e /health) e documentação Swagger (/docs)
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from src.domain.exceptions import ExcecaoEstoque
from src.infrastructure.api.middleware import (
    manipulador_excecao_generica,
    manipulador_excecoes_estoque,
)
from src.infrastructure.api.routers import inventory_router


def criar_aplicacao() -> FastAPI:
    app = FastAPI(
        title="API de Controle de Estoque",
        description=(
            "Serviço para controle consistente e atômico de estoque de produtos, "
            "com suporte a múltiplos estados (Disponível, Reservado e Bloqueado) "
            "e tratamento de alta concorrência."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Registro de manipuladores globais de exceção
    app.add_exception_handler(ExcecaoEstoque, manipulador_excecoes_estoque)
    app.add_exception_handler(Exception, manipulador_excecao_generica)

    # Inclusão das rotas da API
    app.include_router(inventory_router)

    @app.get("/saude", tags=["Monitoramento"], summary="Verificação de integridade do serviço (Healthcheck)")
    @app.get("/health", tags=["Monitoramento"], summary="Healthcheck (compatibilidade)")
    def verificar_saude() -> dict:
        return {"status": "saudavel", "servico": "controle-de-estoque"}

    return app


app = criar_aplicacao()
create_app = criar_aplicacao

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.infrastructure.api.main:app", host="127.0.0.1", port=8000, reload=True)
