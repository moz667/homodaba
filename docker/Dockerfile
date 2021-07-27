FROM python:3.8.3

RUN apt-get update && \
    apt-get -y --no-install-recommends install locales rsync git && \
    echo "es_ES.UTF-8 UTF-8\nen_US.UTF-8 UTF-8" > /etc/locale.gen && \
    locale-gen

ARG APP_SRC_PATH=homodaba

ENV PYTHONUNBUFFERED 1
ENV SECRET_KEY ${SECRET_KEY}
ENV ES_DSL_HOSTS ${ES_DSL_HOSTS}
ENV ALLOWED_HOSTS ${ALLOWED_HOSTS}

RUN mkdir /opt/app

WORKDIR /opt/app

# Directorio con la bbdd sqlite
ENV SQLITE_ROOT "/opt/app/sqlite"
RUN mkdir ${SQLITE_ROOT}
VOLUME ${SQLITE_ROOT}

# Directorio para labores de importacion, escaneo...
# (csvs con la info de los medios, puntos de montaje de red para scanear...)
ENV IMPORT_ROOT "/opt/app/import"
RUN mkdir ${IMPORT_ROOT}
VOLUME ${IMPORT_ROOT}

# Directorio donde se publican los archivos estaticos de django
ENV STATIC_ROOT "/opt/app/static"
RUN mkdir ${STATIC_ROOT}
VOLUME ${STATIC_ROOT}

RUN git clone https://github.com/moz667/homodaba.git homodaba

RUN pip3 install -r homodaba/python-requirements.txt

EXPOSE 8000

COPY manage.sh /manage.sh
RUN chmod 755 /manage.sh

COPY init-homodaba.sh /init-homodaba.sh
RUN chmod 755 /init-homodaba.sh

COPY init-homodaba-tbot.sh /init-homodaba-tbot.sh
RUN chmod 755 /init-homodaba-tbot.sh
# CMD ["/init-homodaba.sh"]

# Recopilamos los estaticos
RUN /bin/bash -c "export SECRET_KEY=RANDPOM_SHIT; \
python3 /opt/app/homodaba/homodaba/manage.py collectstatic --no-input"