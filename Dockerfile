# Use uma imagem base Python oficial
FROM python:3.9-slim-buster

# Define o diretório de trabalho dentro do contêiner
WORKDIR /app

# Copia o arquivo de requisitos e instala as dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante do código da aplicação
COPY ./app /app/app

# Expõe a porta que o Uvicorn irá escutar
EXPOSE 8000

# Comando para iniciar a aplicação Uvicorn
# $PORT é uma variável de ambiente injetada pelo Render
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]