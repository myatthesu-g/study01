# scripts/fastapi/Dockerfile にあるものとバージョンを合わせてください
FROM python:3.11
RUN mkdir /app
COPY ./app /app
ENV PYTHONPATH=/app
WORKDIR /app

RUN apt-get install libfreetype6-dev
RUN apt-get update && apt-get install -y nodejs npm
RUN npm i -g pyright

RUN pip install --upgrade pip
RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=/opt/poetry python - && \
  cd /usr/local/bin && \
  ln -s /opt/poetry/bin/poetry && \
  poetry config virtualenvs.create false
RUN poetry install --no-root

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7000", "--reload"]
