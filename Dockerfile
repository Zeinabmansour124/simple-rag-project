FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

ENV OLLAMA_BASE_URL=http://host.docker.internal:11434

CMD ["streamlit", "run", "simple-rag.py", "--server.address=0.0.0.0"]