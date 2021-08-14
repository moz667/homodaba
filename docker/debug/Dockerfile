# build node statics
FROM node:10 AS gulp

WORKDIR /src
ADD static/package.json /src/
RUN npm install
ADD static/ /src
RUN npm run build

# build django
FROM python:3.8.3

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

ADD homodaba/python-requirements.txt /opt/app/homodaba/python-requirements.txt

RUN pip3 install -r homodaba/python-requirements.txt

ADD homodaba /opt/app/homodaba

COPY --from=gulp /src/build /opt/app/homodaba/static/build

ENV DJANGO_DEBUG 1

EXPOSE 8000

COPY docker/app/init-homodaba.sh /opt/app/init-homodaba.sh

CMD ["/opt/app/init-homodaba.sh"]