FROM mcr.microsoft.com/devcontainers/python:3.11-trixie

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update

RUN apt-get install --no-install-recommends -y gdal-bin python3-gdal \
    gettext postgresql-client

RUN mkdir /code
WORKDIR /code
COPY requirements.txt requirements-dev.txt ./
RUN pip install --upgrade pip \
    && pip install -r /code/requirements.txt \
    && pip install -r /code/requirements-dev.txt \
    && pip install pip-tools

COPY . .
