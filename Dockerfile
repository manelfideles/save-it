FROM python:3.11.5-slim-bookworm

WORKDIR /app

COPY requirements.txt .

RUN pip --timeout=1000 install -r requirements.txt

COPY . .

EXPOSE 8501

RUN echo "Container 'save.it' is live!"

CMD ["streamlit", "run", "src/main.py"]