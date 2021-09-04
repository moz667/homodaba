# Homodaba docker implementation

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