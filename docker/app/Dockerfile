FROM python:3.8.3

ARG APP_SRC_PATH=homodaba

ENV PYTHONUNBUFFERED 1
ENV SECRET_KEY ${SECRET_KEY}
ENV ES_DSL_HOSTS ${ES_DSL_HOSTS}
ENV ALLOWED_HOSTS ${ALLOWED_HOSTS}

WORKDIR /opt/app

# Directorio con la bbdd sqlite
ENV SQLITE_ROOT "/opt/app/sqlite"
VOLUME ${SQLITE_ROOT}

# Directorio para labores de importacion, escaneo...
# (csvs con la info de los medios, puntos de montaje de red para scanear...)
ENV IMPORT_ROOT "/opt/app/import"
VOLUME ${IMPORT_ROOT}

ADD homodaba/python-requirements.txt /opt/app/homodaba/python-requirements.txt

RUN pip3 install -r homodaba/python-requirements.txt

ADD homodaba /opt/app/homodaba

EXPOSE 8000

COPY homodaba/init-homodaba.sh /opt/app/init-homodaba.sh

CMD ["/opt/app/init-homodaba.sh"]