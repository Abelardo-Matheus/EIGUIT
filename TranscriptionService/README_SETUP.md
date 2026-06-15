# Setup da Transcrição Automática (Guitar Studio)

Esta funcionalidade utiliza uma arquitetura distribuída para processar modelos de Machine Learning sem travar o servidor principal.

## Requisitos de Sistema
1. **Redis**: Necessário para o Celery (Fila de Tarefas).
   - Docker: `docker run -d -p 6379:6379 redis`
2. **Dependências Python**:
   - `pip install fastapi uvicorn celery redis basic-pitch spleeter music21`
3. **Frontend**:
   - `npm install axios @coderline/alphatab`

## Como Executar

### 1. Iniciar o Worker do Celery (O "Cérebro")
Abra um terminal na pasta `TranscriptionService` e execute:
```bash
celery -A tasks worker --loglevel=info -P solo
```
*Nota: Em Windows, o parâmetro `-P solo` ou `-P gevent` é recomendado.*

### 2. Iniciar a API FastAPI
Em outro terminal:
```bash
python main.py
```

### 3. Iniciar o Frontend React
Certifique-se de que o componente `TranscriptionApp.jsx` está integrado ao seu projeto Vite/Create React App e rode `npm start`.

## Estratégias de Otimização

### 1. Processamento Assíncrono (Já Implementado)
O uso do Celery garante que o FastAPI apenas receba o arquivo e retorne um `task_id`. O processamento pesado acontece em um processo separado, permitindo que o servidor responda a outros usuários enquanto a IA trabalha.

### 2. Isolamento com Spleeter
Adicionamos o passo de isolação (`spleeter:4stems`). Isso é crucial porque o `basic-pitch` funciona melhor quando o áudio está "limpo". Ao extrair apenas a guitarra (contida no stem 'other'), a precisão da transcrição aumenta drasticamente.

### 3. Aceleração por GPU
Se o servidor possuir uma GPU NVIDIA, instale as versões de `tensorflow-gpu` compatíveis. O Spleeter e o Basic Pitch detectarão automaticamente o hardware, reduzindo o tempo de transcrição de minutos para segundos.

### 4. Limpeza de Arquivos
Em produção, implemente uma tarefa periódica no Celery (Celery Beat) para deletar os arquivos da pasta `temp_audio` após 24 horas, evitando o consumo excessivo de disco.
