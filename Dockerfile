FROM python:3.11.5-slim-bookworm

# Install curl and set up Poetry
RUN apt-get update && apt-get install -y curl
ENV POETRY_HOME=/opt/poetry
RUN curl -sSL https://install.python-poetry.org | python3 - 
RUN cd /usr/local/bin
RUN ln -s /opt/poetry/bin/poetry
RUN poetry config virtualenvs.create false

WORKDIR /.
COPY poetry.lock pyproject.toml ./

RUN poetry install --no-interaction --no-ansi

COPY . .

EXPOSE 8501

RUN echo "Container 'save.it' is live!"

CMD ["poetry", "run", "streamlit", "run", "src/main.py"]