# Usa uma imagem base oficial do Python
FROM python:3.9-slim

# Define o diretório de trabalho no container
WORKDIR /app

# Copia o arquivo de dependências primeiro para aproveitar o cache do Docker
COPY requirements.txt .

# Instala as dependências
# --no-cache-dir reduz o tamanho da imagem
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante do código da aplicação para o diretório de trabalho
COPY . .

# Expõe a porta em que o Flask estará rodando
EXPOSE 5000

# Comando para rodar a aplicação quando o container iniciar
# Usa eventlet diretamente para garantir que ele seja o servidor WSGI
CMD ["python", "app.py"]