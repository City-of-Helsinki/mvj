# ==============================
FROM helsinki.azurecr.io/ubi9/python-311-gdal:latest AS appbase
# ==============================

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY --chown=default:root requirements*.txt /app/

USER root

RUN dnf install -y \
    nc \
    && dnf clean all

USER default

RUN pip install --no-cache-dir -r /app/requirements.txt \
    && pip install --no-cache-dir -r /app/requirements-prod.txt

COPY --chown=default:root deploy/docker-entrypoint.sh /entrypoint/docker-entrypoint.sh
ENTRYPOINT ["/entrypoint/docker-entrypoint.sh"]

# ==============================
FROM appbase AS staticbuilder
# ==============================

COPY --chown=default:root . /app

USER root
# Create static directory if it doesn't exist and set permissions
RUN mkdir -p /app/static && chown -R default:root /app/static

USER default

RUN python manage.py compilemessages
RUN python manage.py collectstatic --noinput


# ==============================
FROM appbase AS development
# ==============================

COPY --chown=default:root requirements-dev.txt /app/requirements-dev.txt
RUN pip install --no-cache-dir -r /app/requirements-dev.txt

ENV DEV_SERVER=1

COPY --chown=default:root . /app/

USER default

EXPOSE 8080/tcp

# ==============================
FROM appbase AS production
# ==============================

COPY --from=staticbuilder --chown=default:root /app/static /app/static
COPY --from=staticbuilder --chown=default:root /app/locale /app/locale
COPY --chown=default:root . /app/

USER default

EXPOSE 8080/tcp
