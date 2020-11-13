FROM python:3.6

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update \
    && apt-get install --no-install-recommends -y gdal-bin python-gdal python3-gdal \
    && apt-get install --no-install-recommends -y gettext postgresql-client

RUN mkdir /code

COPY requirements.txt requirements-dev.txt /code/

WORKDIR /code

RUN pip install --upgrade pip \
    && pip install -r /code/requirements.txt \
    && pip install -r /code/requirements-dev.txt \
    && pip install pip-tools

COPY . /code
