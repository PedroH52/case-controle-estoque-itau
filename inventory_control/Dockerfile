FROM python:3.12-slim

# Evita geração de bytecode .pyc e força flush imediato de stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

WORKDIR /app

# Instala dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia código-fonte e testes
COPY . .

# Porta padrão de exposição
EXPOSE 8000

# Execução padrão do servidor FastAPI
CMD ["uvicorn", "src.infrastructure.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
