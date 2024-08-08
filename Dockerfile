# ==============================
FROM helsinkitest/python:3.8-slim AS appbase
# ==============================

ENV PYTHONUNBUFFERED 1

WORKDIR /app
RUN mkdir /entrypoint

COPY --chown=appuser:appuser requirements*.txt /app/

RUN apt-install.sh \
    build-essential \
    pkg-config \
    libpq-dev \
    gettext \
    gdal-bin \
    netcat-openbsd \
    python3-gdal \
    postgresql-client \
    && pip install --no-cache-dir -r /app/requirements.txt \
    && pip install --no-cache-dir -r /app/requirements-prod.txt \
    && apt-cleanup.sh build-essential pkg-config

COPY --chown=appuser:appuser deploy/docker-entrypoint.sh /entrypoint/docker-entrypoint.sh
ENTRYPOINT ["/entrypoint/docker-entrypoint.sh"]

# ==============================
FROM appbase AS staticbuilder
# ==============================

ENV VAR_ROOT /app

COPY --chown=appuser:appuser . /app
RUN python manage.py compilemessages
RUN python manage.py collectstatic --noinput


# ==============================
FROM appbase AS development
# ==============================

COPY --chown=appuser:appuser requirements-dev.txt /app/requirements-dev.txt
RUN pip install --no-cache-dir -r /app/requirements-dev.txt

ENV DEV_SERVER=1

COPY --chown=appuser:appuser . /app/

USER appuser

EXPOSE 8080/tcp

# ==============================
FROM appbase AS production
# ==============================

COPY --from=staticbuilder --chown=appuser:appuser /app/static /app/static
COPY --from=staticbuilder --chown=appuser:appuser /app/locale /app/locale
COPY --chown=appuser:appuser . /app/

USER appuser

EXPOSE 8080/tcp
