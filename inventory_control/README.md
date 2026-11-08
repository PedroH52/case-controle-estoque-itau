# 📦 Sistema de Controle de Estoque — Case Itaú

[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com/)
[![Pytest](https://img.shields.io/badge/Testes-35%20Aprovados-brightgreen.svg)](https://pytest.org/)
[![Docker](https://img.shields.io/badge/Docker-Pronto-2496ED.svg)](https://www.docker.com/)
[![Arquitetura](https://img.shields.io/badge/Design-DDD%20%2B%20Clean%20Arch-orange.svg)]()

Solução desenvolvida para o **Case Prático de Engenharia de Software (Processo Seletivo Itaú)**.  
Gerencia múltiplos estados de estoque (**Disponível**, **Reservado** e **Bloqueado**), garantindo consistência matemática rigorosa e segurança sob alta concorrência (*thread-safety*).

---

## ⚡ Início Rápido (Execução em 1 Minuto)

Se você está avaliando o projeto no **Windows**:
1. Dê dois cliques em **`CLIQUE_AQUI_PARA_INICIAR.bat`** (ou `iniciar_servidor.bat`).
2. O servidor subirá e **abrirá o seu navegador automaticamente** na documentação interativa:  
   👉 **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)**
3. Para rodar a demonstração com concorrência: clique duas vezes em **`rodar_demo.bat`**.
4. Para rodar os 35 testes automatizados: clique duas vezes em **`rodar_testes.bat`**.

---

## 1. Visão Geral da Solução

O sistema implementa o ciclo de vida completo de movimentação de produtos, assegurando que nenhuma operação coloque o estoque em estado inconsistente ou negativo.

### A Regra Fundamental (Invariante do Domínio)
Em todas as operações (sem exceção), o estoque obedece à equação:

$$\mathbf{Quantidade\ Total} = \mathbf{Disponível} + \mathbf{Reservada} + \mathbf{Bloqueada}$$

### Operações Suportadas
| Operação | Descrição | Regra de Negócio | Endpoint REST |
| :--- | :--- | :--- | :--- |
| **1. Entrada** | Adiciona unidades físicas | Incrementa o estoque *Total* e *Disponível* | `POST /produtos/{id}/estoque/entrada` |
| **2. Saída** | Retirada definitiva por venda/baixa | Apenas permitida se $Disponível \ge Solicitado$ | `POST /produtos/{id}/estoque/saida` |
| **3. Reservar** | Segura estoque para um pedido | Transfere de *Disponível* para *Reservado* (gera UUID) | `POST /produtos/{id}/reservas` |
| **4. Bloquear** | Isola itens para inspeção/avaria | Transfere de *Disponível* para *Bloqueado* (gera UUID) | `POST /produtos/{id}/bloqueios` |
| **5. Liberar** | Cancela reserva ou bloqueio | Devolve a quantidade exata para o *Disponível* | `DELETE .../reservas/{id}`<br>`DELETE .../bloqueios/{id}` |
| **6. Consultar** | Visão instantânea do produto | Retorna Total, Disp, Res, Blq e listas ativas | `GET /produtos/{id}` |

---

## 2. Arquitetura e Estrutura do Código

A solução utiliza **Domain-Driven Design (DDD)** e **Clean Architecture**. A regra de negócio é o núcleo da aplicação e não depende de banco de dados, bibliotecas web ou detalhes externos.

```
inventory_control/
├── src/
│   ├── domain/               # 🧠 NÚCLEO: Regras de negócio puras (Zero dependências externas)
│   │   ├── entities/         # ItemEstoque (Agregado Raiz com trava atômica RLock)
│   │   ├── exceptions/       # Exceções semânticas em português
│   │   └── repositories/     # Interface abstrata (Porta) RepositorioEstoque
│   │
│   ├── application/          # ⚙️ CASOS DE USO: Orquestração e Contratos
│   │   ├── dtos/             # Schemas Pydantic v2 (Validação de entrada/saída)
│   │   └── use_cases/        # ServicoEstoque (Coordena entidades e repositório)
│   │
│   └── infrastructure/       # 🔌 ADAPTADORES: Frameworks, APIs e Persistência
│       ├── persistence/      # RepositorioEstoqueEmMemoria (Thread-safe)
│       └── api/              # FastAPI, Rotas REST e Middleware de Exceções
│
├── tests/                    # 🧪 TESTES AUTOMATIZADOS (35 testes, 100% aprovados)
│   ├── unit/domain/          # Testes unitários do agregado e testes de alta concorrência
│   └── integration/          # Testes de integração dos endpoints e códigos HTTP
│
├── demo.py                   # Script de demonstração visual e interativa
├── CLIQUE_AQUI_PARA_INICIAR.bat # Executável 1-clique para o avaliador
├── Dockerfile & compose      # Conteinerização para execução isolada
└── requirements.txt          # Dependências do projeto
```

---

## 3. Principais Decisões Técnicas

| Decisão | Escolha | Por que essa escolha? (Justificativa Pragmática) |
| :--- | :--- | :--- |
| **Linguagem** | **Python 3.12** | Tipagem estática moderna (`Type Hints`), clareza de leitura, concorrência nativa e execução veloz de testes. |
| **Framework Web** | **FastAPI + Pydantic v2** | Alta performance, validação automática de dados na borda e Swagger interativo gerado nativamente em `/docs`. |
| **Concorrência** | **`threading.RLock` no Agregado** | A trava fica **dentro da entidade de domínio** (`ItemEstoque`), garantindo que checagem e reserva sejam atômicas. Evita *race conditions* mesmo com 50+ requisições concorrentes. |
| **Persistência** | **Repository Pattern (In-Memory)** | Permite ao avaliador rodar a aplicação e 35 testes em **0,5 segundo** sem precisar instalar PostgreSQL ou subir containers externos. A substituição por banco real não altera o domínio. |

---

## 4. Premissas Consideradas

1. **Rastreabilidade por UUIDv4**: Cada reserva ou bloqueio recebe um identificador único imutável, permitindo consultas e liberações seguras.
2. **Atomicidade (*Fail-Fast*)**: Se uma validação falhar (ex: saldo insuficiente), a operação é cancelada imediatamente e o estado anterior é 100% preservado.
3. **Valores Inteiros Positivos**: Quantidades de estoque são números inteiros $> 0$. Estoque de itens discretos não admite frações para evitar imprecisões de ponto flutuante.
4. **Liberação Reversa Precisa**: Liberar uma reserva devolve exatamente o número de itens reservado àquele identificador.

---

## 5. Limitações do Escopo (MVP)

* **Armazenamento em Memória**: Ideal para testes e avaliação local rápida, mas os dados não persistem caso o processo seja finalizado.
* **Escopo Single-Node**: A trava de concorrência atual protege threads no mesmo processo. Para clusters distribuídos (múltiplas réplicas), usa-se trava no banco ou Redis (ver Seção 7).
* **Expiração de Reserva (TTL)**: A liberação é manual via endpoint. Em e-commerces reais, reservas costumam expirar automaticamente após 15 minutos via fila/scheduler.

---

## 6. Instruções Detalhadas de Execução

### Opção 1: Via Terminal (Python Local)
```bash
# 1. Entre na pasta do projeto
cd "inventory_control"

# 2. Instale as dependências
pip install -r requirements.txt

# 3. Execute a suíte de 35 testes (executa em ~0.5s)
python -m pytest

# 4. Inicie o servidor
python run.py
```
> O Swagger abrirá em: **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)**

### Opção 2: Via Docker
```bash
# Subir o contêiner
docker compose up --build -d

# Rodar os testes dentro do Docker
docker compose exec inventory-service pytest

# Verificar saúde da aplicação
curl http://localhost:8000/saude
```

---

## 7. Evolução para um Ambiente de Produção Real

Para operar em escala corporativa no ecossistema **Itaú**, a solução evoluiria da seguinte forma:

```
[ API Gateway / CDN ]
        │
        ▼
[ Microsserviço de Estoque (Kubernetes HPA - Múltiplos Pods) ]
   ├── Persistência Durável: PostgreSQL com SELECT ... FOR UPDATE (Transações ACID)
   ├── Concorrência de Alta Demanda: Redis Distribuído (Redlock para eventos de pico)
   ├── Arquitetura a Eventos (EDA): Apache Kafka (Outbox Pattern: EstoqueReservadoEvent)
   └── Observabilidade: OpenTelemetry (Tracing), Prometheus (Métricas) e Grafana
```

1. **Persistência Transacional (PostgreSQL)**:
   - Uso de `SELECT ... FOR UPDATE` para travar a linha do produto no banco durante saídas e reservas entre múltiplos servidores.
2. **Mensageria Assíncrona (Apache Kafka)**:
   - Notificação desacoplada para sistemas de Pagamentos, Faturamento e Logística via eventos de domínio.
3. **Expiração Automática com Redis**:
   - TTL de 15 minutos em chaves de reserva com notificação automática de expiração (*Keyspace Notifications*).
4. **Observabilidade Total**:
   - Rastreamento distribuído com **OpenTelemetry** e métricas de negócio no **Prometheus** (ex: volume de reservas/minuto, taxa de rejeição por estoque insuficiente).

---

## 8. Uso Crítico de Inteligência Artificial

Conforme orientado no case, a Inteligência Artificial foi utilizada ativamente como ferramenta de aceleração de engenharia e co-piloto técnico.

* **Ferramentas de IA Utilizadas**: **Claude (Anthropic)** e **Gemini (Google)** integrados no ambiente de desenvolvimento como assistentes de engenharia e pair programming.

* **Onde a IA mais agregou**:
  - Aceleração no desenho dos contratos DTOs (Pydantic v2) e endpoints FastAPI.
  - Estruturação do teste de estresse de concorrência com `ThreadPoolExecutor` simulando disputa real de estoque por 50 threads.
* **Sugestões da IA modificadas ou rejeitadas**:
  - *Sugestão Rejeitada 1*: A IA sugeriu aplicar o Lock na camada de Serviço (`ServicoEstoque`). **Decisão**: Rejeitado e movido para o **Agregado Raiz (`ItemEstoque`)** no domínio, pois a proteção dos invariantes pertence ao modelo de negócio, e não a controladores externos.
  - *Sugestão Rejeitada 2*: A IA propôs usar números de ponto flutuante (`float`) para quantidades. **Decisão**: Rejeitado, mantendo estritamente `int` para prevenir erros de precisão IEEE 754.
* **Limitações superadas**:
  - A IA inicialmente gerou testes de API usando o cliente assíncrono do AnyIO que sofria deadlock no Windows Sandbox. Foi necessária intervenção para padronizar os testes com injeção direta de dependência, resultando em testes determinísticos e imediatos (0,49s).

---

## 9. Visão de Engenharia (5 Pilares Adotados)

1. **Blindagem de Invariantes (DDD)**: O estado do estoque só muda por métodos de negócio do Agregado Raiz. Nenhuma camada externa consegue violar a equação do total.
2. **Segurança Concorrente (*Thread-Safety*)**: Proteção contra *race conditions* e venda além do disponível (*overselling*), vital para operações financeiras.
3. **Baixo Acoplamento e Alta Testabilidade**: Domínio 100% puro. O repositório em memória viabiliza testes ultrarrápidos sem mocks complexos.
4. **Comunicação Expressiva (*Fail-Fast*)**: Exceções com causa clara em português e códigos HTTP adequados (400, 404, 409, 422), sem vazamento de stacktrace interno.
5. **Pragmatismo**: Solução completa, limpa e que entrega exatamente o que o case avalia em 3 horas, com caminho documentado para evolução em nuvem.
