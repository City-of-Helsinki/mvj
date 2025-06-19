# ==============================
FROM helsinki.azurecr.io/ubi9/python-311-gdal:latest AS appbase
# ==============================

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY --chown=default:root requirements.txt /app/

USER root

RUN dnf install -y \
    nc \
    && dnf clean all

USER default

RUN pip install --no-cache-dir -r /app/requirements.txt

COPY --chown=default:root docker/qcluster/docker-entrypoint.sh /entrypoint/docker-entrypoint.sh
ENTRYPOINT ["/entrypoint/docker-entrypoint.sh"]

# ==============================
FROM appbase AS staticbuilder
# ==============================

COPY --chown=default:root . /app

USER root

# Create the media directory if it doesn't exist and set permissions
RUN mkdir -p /mvj-media && chown -R default:root /mvj-media

USER default

RUN python manage.py compilemessages

# ==============================
FROM appbase AS production
# ==============================

COPY --from=staticbuilder --chown=default:root /app/locale /app/locale
COPY --chown=default:root . /app/
