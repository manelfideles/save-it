FROM python:3.11.5-slim-bookworm

WORKDIR /app

COPY requirements.txt .

# 3h timeout
RUN pip --timeout=10800 install -r requirements.txt

COPY . .

EXPOSE 8501

RUN echo "Container 'save.it' is live!"

# Explicitly set the server address
CMD ["streamlit", "run", "src/main.py"]