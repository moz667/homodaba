FROM python:3.8.3-alpine3.12

ARG APP_SRC_PATH=homodaba

ENV PYTHONUNBUFFERED=1 \
  SECRET_KEY=${SECRET_KEY} \
  ES_DSL_HOSTS=${ES_DSL_HOSTS} \
  ALLOWED_HOSTS=${ALLOWED_HOSTS} \
  SQLITE_ROOT="/opt/app/sqlite" \
  IMPORT_ROOT="/opt/app/import"

WORKDIR /opt/app

# Directorio con la bbdd sqlite
VOLUME ${SQLITE_ROOT}

# Directorio para labores de importacion, escaneo...
# (csvs con la info de los medios, puntos de montaje de red para scanear...)
VOLUME ${IMPORT_ROOT}

# Instalacion basica (django + sqlite):
ADD homodaba/requirements.txt /opt/app/homodaba/requirements.txt
RUN apk add build-base libxml2-dev libxslt-dev
RUN pip3 install -r homodaba/requirements.txt

# Mysql:
ADD homodaba/requirements-mysql.txt /opt/app/homodaba/requirements-mysql.txt
ARG DATABASE_ENGINE
RUN if [ "$DATABASE_ENGINE" = "mysql" ]; then \
      apk add mariadb-client mariadb-dev && \
      pip3 install -r homodaba/requirements-mysql.txt; \
    fi

# TODO: Todo esto esta sin probar... VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV
# Seguramente tendremos que meter algun apk add mas :P

# Elastic search:
ADD homodaba/requirements-elasticsearch.txt /opt/app/homodaba/requirements-elasticsearch.txt
ARG ELASTICSEARCH
RUN if [ "$ELASTICSEARCH" != "" -a "$ELASTICSEARCH" != "false" ]; then \
      pip3 install -r homodaba/requirements-elasticsearch.txt; \
    fi

# Telegram:
ADD homodaba/requirements-telegram.txt /opt/app/homodaba/requirements-telegram.txt
ARG TELEGRAM
RUN if [ "$TELEGRAM" != "" -a "$TELEGRAM" != "false" ]; then \
      pip3 install -r homodaba/requirements-telegram.txt; \
    fi

# TODO: Todo esto esta sin probar... ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


ADD homodaba /opt/app/homodaba

EXPOSE 8000

COPY docker/app/init-homodaba.sh /opt/app/init-homodaba.sh

CMD ["/opt/app/init-homodaba.sh"]
