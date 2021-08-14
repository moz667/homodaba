# build node statics
FROM node:10 AS gulp

WORKDIR /src
ADD static/package.json /src/
RUN npm install
ADD static/ /src
RUN npm run build

# build django statics
FROM python:3.8.3 AS django

ENV STATIC_ROOT="/tmp/static" \
    SECRET_KEY="**NONE**"
WORKDIR /src
ADD homodaba/python-requirements.txt /src/python-requirements.txt
RUN pip3 install -r python-requirements.txt
ADD homodaba/ /src/
COPY --from=gulp /src/build /src/static/build
RUN mkdir -p "$STATIC_ROOT" && python manage.py collectstatic --no-input

# final stage
FROM nginx

COPY docker/proxy/nginx.conf /etc/nginx/nginx.conf
COPY --from=django /tmp/static /www/public/static
RUN gzip -6 -k $(find /www/public -name *.html -o -name *.css -o -name *.js -o -name *.svg -o -name *.ico)

