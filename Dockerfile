FROM python:3.11.5-slim-bookworm

WORKDIR /app

COPY requirements.txt .

RUN apt-get update && apt-get install -y curl \
    && pip install -r requirements.txt

COPY . .

EXPOSE 8501

RUN echo "Container 'save.it' is live!"

CMD ["streamlit", "run", "src/main.py"]