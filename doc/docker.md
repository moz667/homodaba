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
 - <a name="app-build-args-database-engine"></a>**DATABASE_ENGINE**, choose between available [database engines](https://docs.djangoproject.com/en/3.2/ref/settings/#engine), at the time it would be `sqlite` (default) or `mysql`.
    
 - <a name="app-build-args-elasticsearch"></a>**ELASTICSEARCH**, boolean that add elasticsearch support for a better natural searching experience. The value would be **other than `false`** that enables elasticsearch or `false` thats not (default). **`(Testing)`**

 - <a name="app-build-args-telegram"></a>**TELEGRAM**, boolean that add telegram supports required for launching the telegram bot. The value would be **other than `false`** that enables telegram or `false` thats not (default). **`(Testing)`**

### Environment variables

#### **Secrets:**

> *This are special type of Vars as they hide information of an encrypted format or passwords, **that you would keep secure and store safely and never share**.*

- **SECRET_KEY**, This is used to provide cryptographic signing, and should be set to a unique, unpredictable value. [More info](https://docs.djangoproject.com/en/3.2/ref/settings/#secret-key)

- **TBOT_TOKEN**, The token is a string that is required to authorize the bot and send requests to the Bot API. Keep your token secure and store it safely, it can be used by anyone to control your bot. [More info](https://core.telegram.org/bots#6-botfather)

- **HDB_KODI_API_USER**, username able to connect to homodaba server throught kodi addons (only one at the time). **`(Testing)`**

- **HDB_KODI_API_KEY**, token for auth throught kodi addons (only one at the time). *In testing and must will change*


#### **Homodaba config vars:**

- **DJANGO_DEBUG**, a boolean that turns on/off debug mode. Never deploy a site into production with DJANGO_DEBUG turned on. The value would be `1` that enables debug mode or `0` thats not (default). [More info](https://docs.djangoproject.com/en/3.2/ref/settings/#debug)

- **ALLOWED_HOSTS**, a string representing the host/domain names (separated by space ` `) that this Django site can serve. This is a security measure to prevent HTTP Host header attacks, which are possible even under many seemingly-safe web server configurations. [More info](https://docs.djangoproject.com/en/3.2/ref/settings/#allowed-hosts)

- <a name="app-other-args-sqlite-root"></a>SQLITE_ROOT, the full path to the sqlite database files. Default: the same path than `homodaba/manage.py`.

- **DATABASE_NAME**, the name of the database to use. For SQLite, it’s the full path to the database file. Default: [SQLITE_ROOT](#app-other-args-sqlite-root)`/db.sqlite3`.

- **DATABASE_USER**, the username to use when connecting to the database. Not used with SQLite. Default: '' (Empty string). [More info](https://docs.djangoproject.com/en/3.2/ref/settings/#user)

- **DATABASE_PASSWORD**, The password to use when connecting to the database. Not used with SQLite. Default: '' (Empty string). [More info](https://docs.djangoproject.com/en/3.2/ref/settings/#password)

- **DATABASE_HOST**, which host to use when connecting to the database. An empty string means localhost. Not used with SQLite. Default: '' (Empty string). [More info](https://docs.djangoproject.com/en/3.2/ref/settings/#host)

- **DATABASE_PORT**, the port to use when connecting to the database. An empty string means the default port. Not used with SQLite. Default: '' (Empty string). [More info](https://docs.djangoproject.com/en/3.2/ref/settings/#port)

- **ADMIN_MOVIE_LIST_PER_PAGE**, number of elements (movies) displaying on the admin movie list page. Default: 100.

- **CASTING_LIMIT**, number to limit the casting elements inserted on the database. Default: 10.

- **NO_CACHE**, boolean with values `0` or `1`, for disabled entirely the intermediate cache (for imdb queries). Default: `0` that’s mean the cache is enabled.

- **UPDATE_CACHE**, boolean with values `0` or `1`, for force the update in every single imdb request. Default: `0` that’s mean the cache only updates when it’s the first time we access to an imdb request.

- **CACHE_DATABASE**, boolean with values `0` or `1`, for split the database in alternative database for the intermediate cache. Default: `1` that’s mean the cache is separated from ordinary data.

- **CACHE_DATABASE_ENGINE**, string that define the kind of database it’s using for intermediate cache. Must choose between available [database engines](https://docs.djangoproject.com/en/3.2/ref/settings/#engine), at the time it would be `sqlite` (default) or `mysql`.

- **CACHE_DATABASE_NAME**, the name of the intermediate cache database to use. For SQLite, it’s the full path to the database file. Default: [SQLITE_ROOT](#app-other-args-sqlite-root)`/db-cache.sqlite3`.

- **CACHE_DATABASE_USER**, the username to use when connecting to the intermediate cache database. Not used with SQLite. Default: '' (Empty string). [More info](https://docs.djangoproject.com/en/3.2/ref/settings/#user)

- **CACHE_DATABASE_PASSWORD**, The password to use when connecting to the intermediate cache database. Not used with SQLite. Default: '' (Empty string). [More info](https://docs.djangoproject.com/en/3.2/ref/settings/#password)

- **CACHE_DATABASE_HOST**, which host to use when connecting to the intermediate cache database. An empty string means localhost. Not used with SQLite. Default: '' (Empty string). [More info](https://docs.djangoproject.com/en/3.2/ref/settings/#host)

- **CACHE_DATABASE_PORT**, the port to use when connecting to the intermediate cache database. An empty string means the default port. Not used with SQLite. Default: '' (Empty string). [More info](https://docs.djangoproject.com/en/3.2/ref/settings/#port)

- **HOME_URL_PATH**,

- **SMB_SHARE_2_URL_KEY_X**,

- **SMB_SHARE_2_URL_VALUE_X**,

- **HDB_KODI_SUPPORT**, 

- **TBOT_LIMIT_MOVIES**,

- **IMDB_VALID_MOVIE_KINDS**,

- **LOCALNETIP**,

- **ES_DSL_HOSTS**,

- **HOME_URL_PATH**,

- **STATIC_ROOT**,

- **STATIC_BUILD**,


#### **Hidden vars:**

> This vars exists but will never needed to be defined at docker-compose level. [See build args](#app-build-args)

- [DATABASE_ENGINE](#app-build-args-database-engine)

- [ELASTICSEARCH](#app-build-args-elasticsearch)

- [TELEGRAM](#app-build-args-telegram)

