FROM python:3.11

# ---- uvicorn-gunicorn
ARG IMAGE_TAG='latest'

COPY ./scripts/fastapi/uvicorn-gunicorn-docker/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY ./scripts/fastapi/uvicorn-gunicorn-docker/start.sh /start.sh
RUN chmod +x /start.sh

COPY ./scripts/fastapi/uvicorn-gunicorn-docker/gunicorn_conf.py /gunicorn_conf.py

COPY ./scripts/fastapi/uvicorn-gunicorn-docker/start-reload.sh /start-reload.sh
RUN chmod +x /start-reload.sh

ENV API_TAG_VERSION=${IMAGE_TAG}
# this is for debug
RUN echo "API TAG VERSION: ${API_TAG_VERSION}"

ENV PYTHONPATH=/app
WORKDIR /app
EXPOSE 80

# Run the start script, it will check for an /app/prestart.sh script (e.g. for migrations)
# And then will start Gunicorn with Uvicorn
CMD ["/start.sh"]

# /---- uvicorn-gunicorn

COPY ./fastapi/app/poetry.lock /app/
COPY ./fastapi/app/pyproject.toml /app/
RUN pip install --upgrade pip
RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=/opt/poetry python - && \
  cd /usr/local/bin && \
  ln -s /opt/poetry/bin/poetry && \
  poetry config virtualenvs.create false
RUN poetry install --no-root --no-dev

# Pythonではマイグレーションしないので一旦コメントアウト
#COPY ./fastapi/app/prestart.sh /app/
#RUN chmod +x prestart.sh

COPY ./fastapi/app /app
