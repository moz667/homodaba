FROM python:3.8.3-alpine3.12

ARG APP_SRC_PATH=homodaba
ARG DATABASE_ENGINE
ARG ELASTICSEARCH
ARG TELEGRAM

ENV PYTHONUNBUFFERED=1 \
  SECRET_KEY=${SECRET_KEY} \
  ES_DSL_HOSTS=${ES_DSL_HOSTS} \
  DATABASE_ENGINE=${DATABASE_ENGINE}

WORKDIR /opt/app

# Instalacion basica (django + sqlite):
ADD homodaba/requirements.txt /opt/app/homodaba/requirements.txt
RUN apk add build-base libxml2-dev libxslt-dev
RUN pip3 install -r homodaba/requirements.txt

# Mysql:
ARG DATABASE_ENGINE
ENV DATABASE_ENGINE=$DATABASE_ENGINE
ADD homodaba/requirements-mysql.txt /opt/app/homodaba/requirements-mysql.txt
RUN if [ "$DATABASE_ENGINE" = "mysql" ]; then \
      apk add mariadb-client mariadb-dev && \
      pip3 install -r homodaba/requirements-mysql.txt; \
    fi

# TODO: Todo esto esta sin probar... VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV
# Seguramente tendremos que meter algun apk add mas :P

# Elastic search:
ARG ELASTICSEARCH
ENV ELASTICSEARCH=$ELASTICSEARCH
ADD homodaba/requirements-elasticsearch.txt /opt/app/homodaba/requirements-elasticsearch.txt
RUN if [ "$ELASTICSEARCH" != "" -a "$ELASTICSEARCH" != "false" ]; then \
      pip3 install -r homodaba/requirements-elasticsearch.txt; \
    fi

# Telegram:
ARG TELEGRAM
ENV TELEGRAM=$TELEGRAM
ADD homodaba/requirements-telegram.txt /opt/app/homodaba/requirements-telegram.txt
RUN if [ "$TELEGRAM" != "" -a "$TELEGRAM" != "false" ]; then \
      pip3 install -r homodaba/requirements-telegram.txt; \
    fi

# TODO: Todo esto esta sin probar... ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

ADD homodaba /opt/app/homodaba
ADD static /opt/app/static

EXPOSE 8000

COPY docker/app/init-homodaba.sh /opt/app/init-homodaba.sh
COPY docker/app/sample/sample-data.csv ${IMPORT_ROOT}/sample-data.csv

HEALTHCHECK --start-period=90s CMD wget -q -O /dev/null http://localhost:8000/${HOME_URL_PATH}admin/login/?next=/admin/ || exit 1

CMD ["/opt/app/init-homodaba.sh"]
