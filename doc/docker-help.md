# Ayudas docker

## Construir imagen en local e instalar en servidor

Si tienes un nas limitadito, como el mio, es posible que quieras construir las imagenes fuera del mismo, para poder hacer esto, el unico requisito es tener con el servidor una conexion ssh disponible y ejecutar el siguiente script:

**En local: build-and-deploy.sh**
```bash
#!/bin/bash

REMOTE_SERVER=myserver
REMOTE_SERVER_INSTALL_DIR=/opt/app/homodaba
REMOTE_SERVER_COMPOSE_ARG="-f docker-compose.$REMOTE_SERVER.yml"
LOCAL_PROJECT_DIR=~/homodaba

# homodaba project dir
cd $LOCAL_PROJECT_DIR

# Actualizamos los fuentes de homodaba y damos permisos a static/build
ssh $REMOTE_SERVER "cd $REMOTE_SERVER_INSTALL_DIR && \
    sudo git pull && \
    sudo mkdir -p static/build"

# Copiamos el build de static
rsync -qa --del static/build/ $REMOTE_SERVER:$REMOTE_SERVER_INSTALL_DIR/static/build/

# Hay que construir por cojines... al montar como vol para dev
# aunque use la misma imagen, es presumible que haya cambios
docker compose build

# Copiamos la imagen y arrancamos el compose
docker save homodaba_app | ssh -C $REMOTE_SERVER "docker load && \
    cd $REMOTE_SERVER_INSTALL_DIR && \
    docker compose $REMOTE_SERVER_COMPOSE_ARG up -d && \
    sleep 10 && \
    docker compose $REMOTE_SERVER_COMPOSE_ARG exec python homodaba/manage.py collectstatic --no-input"
```

**En el servidor: docker-compose.$REMOTE_SERVER.yml**

De forma opcional puedes querer definir una infraestructura distinta a la por defecto  trata de la infra de la app que quieras usar, si por ejemplo quieres tener carpetas para mantener los datos como volumes, este seria un buen sitio para ponerlo.
En este caso mostrado a continuacion (y que es compatible con el script anterior) tenemos:

* ./static/publish para poder servir los estaticos a traves de un proxy inverso
* ./import una carpeta donde poder importar datos
* ./sqlite la base de datos actual (incluida la cache en este caso)

**Ejemplo de archivo:  docker-compose.myserver.yml**

```yml
version: '2.1'

services:
  app:
    extends:
      service: app
      file: docker-compose.yml
    volumes:
      - ./static/publish:/opt/app/static/publish
      - ./import:/opt/app/import
      - ./sqlite:/opt/app/sqlite
    env_file:
      - .env
```
