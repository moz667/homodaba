#### Legend
> **`(Testing)`** feature in testing, thats means that would be change.

# Homodaba docker implementation
## Service app
```yaml
app:
    build:
        context: .
        dockerfile: docker/app/Dockerfile
        args:
            DATABASE_ENGINE: ${DATABASE_ENGINE:-sqlite}
            ELASTICSEARCH: ${ELASTICSEARCH:-false}
            TELEGRAM: ${TELEGRAM:-false}
    environment:
        ALLOWED_HOSTS: "${ALLOWED_HOSTS:-127.0.0.1 localhost}"
    volumes:
        - /opt/app/import
        - /opt/app/sqlite
```
### <a name="app-build-args"></a>Building arguments
 - <a name="app-build-args-database-engine"></a>DATABASE_ENGINE, choose between available [database engines](https://docs.djangoproject.com/en/3.2/ref/settings/#engine), at the time it would be `sqlite` (default) or `mysql`.
    
 - <a name="app-build-args-elasticsearch"></a>ELASTICSEARCH, boolean that add elasticsearch support for a better natural searching experience. The value would be **other than `false`** that enables elasticsearch or `false` thats not (default). **`(Testing)`**

 - <a name="app-build-args-telegram"></a>TELEGRAM, boolean that add telegram supports required for launching the telegram bot. The value would be **other than `false`** that enables telegram or `false` thats not (default). **`(Testing)`**

### Environment variables

#### Secrets:

> *This are special type of Vars as they hide information of an encrypted format or passwords, **that you would keep secure and store safely and never share**.*

- SECRET_KEY, This is used to provide cryptographic signing, and should be set to a unique, unpredictable value. [More info](https://docs.djangoproject.com/en/3.2/ref/settings/#secret-key)

- TBOT_TOKEN, The token is a string that is required to authorize the bot and send requests to the Bot API. Keep your token secure and store it safely, it can be used by anyone to control your bot. [More info](https://core.telegram.org/bots#6-botfather)

- HDB_KODI_API_USER, username able to connect to homodaba server throught kodi addons (only one at the time). **`(Testing)`**

- HDB_KODI_API_KEY, token for auth throught kodi addons (only one at the time). *In testing and must will change*

**Other vars:**

- DJANGO_DEBUG, a boolean that turns on/off debug mode. Never deploy a site into production with DJANGO_DEBUG turned on. The value would be `1` that enables debug mode or `0` thats not (default). [More info](https://docs.djangoproject.com/en/3.2/ref/settings/#debug)

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

**Hidden vars:**
> This vars exists but will never needed to be defined at docker-compose level. [See build args](#app-build-args)
 - [DATABASE_ENGINE](#app-build-args-database-engine)
 - [ELASTICSEARCH](#app-build-args-elasticsearch)
 - [TELEGRAM](#app-build-args-telegram)

