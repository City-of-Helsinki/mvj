FROM mcr.microsoft.com/devcontainers/python:3.10-bookworm

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update

# Force pynacl to use the system libsodium to make installation work on ARM CPUs
# https://github.com/pyca/pynacl/issues/553
RUN apt-get install --yes libsodium-dev
RUN SODIUM_INSTALL=system pip3 install pynacl==1.3.0

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
