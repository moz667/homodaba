#### Legend

> **`(Testing)`**: It’s use to mark a feature in testing mode. Keep in mind thats means that it could change.


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
    volumes:
        - /opt/app/import
        - /opt/app/sqlite
```


### <a name="app-build-args"></a>Building arguments
 - <a name="app-build-args-database-engine"></a>**DATABASE_ENGINE**, string to choose between available [database engines](https://docs.djangoproject.com/en/3.2/ref/settings/#engine). At the time it would be `sqlite` (default) or `mysql`.
    
 - <a name="app-build-args-elasticsearch"></a>**ELASTICSEARCH**, boolean that add elasticsearch support for a better natural searching experience. The value would be **other than `false`** that enables elasticsearch or `false` thats disable elasticsearch. Default: `false`. **`(Testing)`**

 - <a name="app-build-args-telegram"></a>**TELEGRAM**, boolean that add telegram supports required for launching the telegram bot. The value would be **other than `false`** that enables telegram or `false`  thats disable telegram support. Default: `false`. **`(Testing)`**


### Environment variables

#### **Secrets:**

> *This are special type of Vars as they hide information of an encrypted format or passwords, **which you should keep secure and store safely and never share**.*

- **SECRET_KEY**, This is used to provide cryptographic signing, and should be set to a unique, unpredictable value. [More info](https://docs.djangoproject.com/en/3.2/ref/settings/#secret-key)

- **TBOT_TOKEN**, The token is a string that is required to authorize the bot and send requests to the Bot API. Keep your token secure and store it safely, it can be used by anyone to control your bot. [More info](https://core.telegram.org/bots#6-botfather)

- **HDB_KODI_API_USER**, username able to connect to homodaba server throught kodi addons (Only one at this time). **`(Testing)`**

- **HDB_KODI_API_KEY**, token for auth throught kodi addons (Only one at this time). **`(Testing)`**

#### **Homodaba config vars:**

> *Variables for config the main application or that affect the behavior of it self.*

- **DJANGO_DEBUG**, a boolean that turns on/off debug mode. Never deploy a site into production with DJANGO_DEBUG turned on. The value would be `1` that enables debug mode or `0` thats disable debug mode. Default: `0`. [More info](https://docs.djangoproject.com/en/3.2/ref/settings/#debug)

- **ALLOWED_HOSTS**, a string representing the host/domain names separated by `' '` (Space)) that this Django site can serve. This is a security measure to prevent HTTP Host header attacks, which are possible even under many seemingly-safe web server configurations. [More info](https://docs.djangoproject.com/en/3.2/ref/settings/#allowed-hosts)

- <a name="app-other-args-sqlite-root"></a>**SQLITE_ROOT**, string with the path to the sqlite database files. Default: `../sqlite` (`/opt/app/sqlite` absolute path from the container persepective).

- **DATABASE_NAME**, string with the name of the database to use. For SQLite, it’s the path to the database file with the file name. Default: [SQLITE_ROOT](#app-other-args-sqlite-root)`/db.sqlite3`.

- **DATABASE_USER**, string with the username to use when connecting to the database. Not used with SQLite. Default: `''` (Empty string). [More info](https://docs.djangoproject.com/en/3.2/ref/settings/#user)

- **DATABASE_PASSWORD**, string with the password to use when connecting to the database. Not used with SQLite. Default: `''` (Empty string). [More info](https://docs.djangoproject.com/en/3.2/ref/settings/#password)

- **DATABASE_HOST**, string with the name of the host to use when connecting to the database. An empty string means localhost. Not used with SQLite. Default: `''` (Empty string). [More info](https://docs.djangoproject.com/en/3.2/ref/settings/#host)

- **DATABASE_PORT**, string with the port to use when connecting to the database. An empty string means the default port. Not used with SQLite. Default: `''` (Empty string). [More info](https://docs.djangoproject.com/en/3.2/ref/settings/#port)

- **ADMIN_MOVIE_LIST_PER_PAGE**, integer with the number of elements (movies) displaying on the admin movie list page. Default: `100`.

- **CASTING_LIMIT**, integer with the number to limit the casting elements inserted on the database. Default: `10`.

- **NO_CACHE**, boolean with values `0` or `1`, for disabled entirely the intermediate cache (for IMDb queries). Default: `0` that’s mean the cache is enabled.

- **UPDATE_CACHE**, boolean with values `0` or `1`, for force the update in every single IMDb request. Default: `0` that’s mean the cache only updates when it’s the first time we access to an IMDb request.

- **CACHE_DATABASE**, boolean with values `0` or `1`, for split the database in alternative database for the intermediate cache. Default: `1` that’s mean the cache is separated from the rest of the data.

- **CACHE_DATABASE_ENGINE**, string that define the kind of database it’s using for intermediate cache. Must choose between available [database engines](https://docs.djangoproject.com/en/3.2/ref/settings/#engine), at the time it would be `sqlite` or `mysql`. Default: `'sqlite'`.

- **CACHE_DATABASE_NAME**, string that define the file name of the intermediate cache database to use. For SQLite, it’s the path to the database file with the file name. Default: [SQLITE_ROOT](#app-other-args-sqlite-root)`/db-cache.sqlite3`.

- **CACHE_DATABASE_USER**, string with the username to use when connecting to the intermediate cache database. Not used with SQLite. Default: `''` (Empty string). [More info](https://docs.djangoproject.com/en/3.2/ref/settings/#user)

- **CACHE_DATABASE_PASSWORD**, string with the password to use when connecting to the intermediate cache database. Not used with SQLite. Default: `''` (Empty string). [More info](https://docs.djangoproject.com/en/3.2/ref/settings/#password)

- **CACHE_DATABASE_HOST**, string with the name of the host to use when connecting to the intermediate cache database. An empty string means localhost. Not used with SQLite. Default: `''` (Empty string). [More info](https://docs.djangoproject.com/en/3.2/ref/settings/#host)

- **CACHE_DATABASE_PORT**, string with the port to use when connecting to the intermediate cache database. An empty string means the default port. Not used with SQLite. Default: `''` (Empty string). [More info](https://docs.djangoproject.com/en/3.2/ref/settings/#port)

- **HOME_URL_PATH**, string to define the absolute path where is mapping the app in the webserver. Usefull for sharing a same domain between various apps. Default: `''` (Empty string). 

- **HDB_KODI_SUPPORT**, boolean with values `0` or `1`, to enable kodi supports. Default: `0` that’s mean kodi support is disabled.

- **TBOT_LIMIT_MOVIES**, integer to limit the results of telegram bot queries. Default: `10` that’s mean  is limited to 10 results. **`(Testing)`**

- **IMDB_VALID_MOVIE_KINDS**, string with the kind of movies that we are looking for more frequently. This is usefull for faster matches with the IMDb queries. It can contain several types separated by `','` (Comma). Default: `movie`. [More info](https://IMDbpy.readthedocs.io/en/latest/usage/movie.html?highlight=kind#movies)

- **ES_DSL_HOSTS**, string with the host (ip address or name) of the elastic search server, also, if it has any value, it assumes that you will use elasticsearch as a search engine. Default: `''` (Empty string). **`(Testing)`**

- <a name="app-config-vars-static-root"></a>**STATIC_ROOT**, string with the path to all the collected static files (css, js, imgs...) of the homodaba app. Default: `../static/publish` (`/opt/app/static/publish` absolute path from the container persepective). [More info](https://docs.djangoproject.com/en/3.2/ref/settings/#static-root)

- **STATIC_BUILD**, string with the path to the generated static files (css, js, imgs...) of the homodaba app. Default: `../static/build` (`/opt/app/static/build` absolute path from the container persepective).


#### **Hidden vars:**

> This vars exists but will never needed to be defined at docker-compose level. [See build args](#app-build-args)

- [DATABASE_ENGINE](#app-build-args-database-engine)

- [ELASTICSEARCH](#app-build-args-elasticsearch)

- [TELEGRAM](#app-build-args-telegram)



### Volumes

> There are some interesting volumes that you will consider mapping when run the container, those volumes are:

* `/opt/app/static/publish`, path where all the static files are collected. (See also: [STATIC_ROOT](#app-config-vars-static-root))

* `/opt/app/import`, path to simplify the process of importing data to the app.

* `/opt/app/sqlite`, path where de sqlite files are stored. (See also: [SQLITE_ROOT](#app-other-args-sqlite-root))
