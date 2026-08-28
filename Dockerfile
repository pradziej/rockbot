FROM python:3.10-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir .

RUN useradd --create-home --shell /usr/sbin/nologin rockbot
USER rockbot

ENTRYPOINT ["rockbot"]
