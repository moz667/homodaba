# build node statics
FROM node:10 AS gulp

WORKDIR /src
ADD static/package*.json /src/
RUN npm clean-install
ADD static/ /src
RUN npm run build

# build django statics
FROM python:3.8.3-alpine3.12 AS django

ENV STATIC_ROOT="/tmp/static" \
    SECRET_KEY="**NONE**" \
    STATIC_BUILD="./static/build"

WORKDIR /src

ADD homodaba/requirements.txt /src/homodaba/requirements.txt
RUN apk add build-base libxml2-dev libxslt-dev
RUN pip3 install -r homodaba/requirements.txt

ADD homodaba/ /src/
COPY --from=gulp /src/build /src/static/build
RUN mkdir -p "$STATIC_ROOT" && python manage.py collectstatic --no-input

# final stage
FROM nginx

COPY docker/proxy/nginx.conf /etc/nginx/nginx.conf
COPY --from=django /tmp/static /www/public/static

HEALTHCHECK CMD curl --fail http://localhost:80/ || exit 1

RUN gzip -6 -k $(find /www/public -name *.html -o -name *.css -o -name *.js -o -name *.svg -o -name *.ico)

