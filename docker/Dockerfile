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
ENV SQLITE3_PATH "/opt/app/sqlite3"

RUN mkdir /opt/app

WORKDIR /opt/app
RUN mkdir /opt/app/sqlite3

RUN git clone https://github.com/moz667/homodaba.git homodaba

RUN pip3 install -r homodaba/python-requirements.txt

VOLUME /opt/app/sqlite3

EXPOSE 8000

COPY manage.sh /manage.sh
RUN chmod 755 /manage.sh

COPY init-homodaba.sh /init-homodaba.sh
RUN chmod 755 /init-homodaba.sh
CMD ["/init-homodaba.sh"]
