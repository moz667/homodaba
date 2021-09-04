# Homodaba docker implementation

@bpk667 A ver que piensas acerca de esto:

Despues de toda la chapa que os he dado con las variables de entorno con docker y docker compose he llegado a la siguiente conclusion: 

**Los secretos no se deben definir nunca como environment en `docker-compose.base`.**

Esto se debe a que si los defines ahí, aunque sea solamente definiendo los como `SECRET_KEY: ${SECRET_KEY?Variable not set}`, te vas ver obligado a poner los secretos en `.env` o a pasarle a docker-compose el argumento `--env-file .app.secrets.env` en cualquiera de los dos casos, vas a estar compartiendo los secretos con todos los servicios que arranques en compose, lo cual no mola nada.

O al menos es a la conclusion que he llegado despues de estar pegandome con ello.

Comentame como lo ves y esta vez voy a librar a p4u con mis molestos mensajes de telegram reiniciando el dia de la marmota ^_^

Este mensaje lo he metido en el docu (porque queria probar a ver si te hace mention github) aunque lo voy a poner como comentario despues :P

> BTW: A partir de ahora, voy a intentar documentar y comentar en el code en mi moz-english for dummies, y, como tu la tienes infinitamente mas larga que yo en ese aspecto, mi culito espera que me fustigues con correcciones ;). Los comentarios que te haga directos, por el bien de los dos, van a seguir siendo en castellano.

## Service app

### Environment variables

#### Secrets:

> *This are special type of Vars as they hide information of an encrypted format or passwords, **that you would keep secure and store safely and never share**.*

- SECRET_KEY, This is used to provide cryptographic signing, and should be set to a unique, unpredictable value. [More info](https://docs.djangoproject.com/en/3.2/ref/settings/#secret-key)

- TBOT_TOKEN, The token is a string that is required to authorize the bot and send requests to the Bot API. Keep your token secure and store it safely, it can be used by anyone to control your bot. [More info](https://core.telegram.org/bots#6-botfather)

- HDB_KODI_API_USER, username able to connect to homodaba server throught kodi addons (only one at the time). *In testing and must will change*

- HDB_KODI_API_KEY, token for auth throught kodi addons (only one at the time). *In testing and must will change*

**Other vars:**

- DJANGO_DEBUG, (0,1) A boolean that turns on/off debug mode. Never deploy a site into production with DJANGO_DEBUG turned on. [More info](https://docs.djangoproject.com/en/3.2/ref/settings/#debug)

- DATABASE_HOST, TODO:
- DATABASE_NAME, TODO:
- ADMIN_MOVIE_LIST_PER_PAGE, TODO:
- CACHE_DATABASE, TODO:
- HOST_SQLITE, TODO:
- HOST_IMPORT, TODO:
- HOME_URL_PATH, TODO:
- SMB_SHARE_2_URL_KEY_1, TODO:
- SMB_SHARE_2_URL_VALUE_1, TODO:
- HDB_KODI_SUPPORT, TODO: