"""
Django settings for homodaba project.

Generated by 'django-admin startproject' using Django 3.1.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.1/ref/settings/
"""

from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve(strict=True).parent.parent

TBOT_TOKEN = os.getenv("TBOT_TOKEN", "")
TBOT_LIMIT_MOVIES = int(os.getenv("TBOT_LIMIT_MOVIES", "10"))

ADMIN_MOVIE_LIST_PER_PAGE = int(os.getenv("ADMIN_MOVIE_LIST_PER_PAGE", "100"))

# Tipos de pelicula que consideramos buenos. [por defecto: movie]
# imdb tiene muchos tipos: movie, tv movie, video... en principio
# esta guay usar solo movie para las peliculas porque es una forma
# sencilla de filtrar los resultados de las busquedas para encontrar
# buenos matches en el casos de peliculas (usando solo movie)
IMDB_VALID_MOVIE_KINDS = os.getenv("IMDB_VALID_MOVIE_KINDS", 'movie').split(',')

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False if os.getenv("DJANGO_DEBUG", '1') == '0' else True

LOCALNETIP = os.getenv("LOCALNETIP", '127.0.0.1')
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', LOCALNETIP).split()

# Application definition

INSTALLED_APPS = [
    'admin_interface',
    'colorfield',
    'data.apps.DataConfig',
    'tbot.apps.TbotConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'admin_auto_filters',
    # 'easy_select2',
    # 'tagging', TODO: quitar de requeriments... no lo vamos a usar
]

elasticsearch_hosts = os.getenv("ES_DSL_HOSTS", False)
if elasticsearch_hosts:
    INSTALLED_APPS.append('django_elasticsearch_dsl')

    ELASTICSEARCH_DSL = {
        'default': {
            'hosts': elasticsearch_hosts
        },
    }
else:
    ELASTICSEARCH_DSL = False

X_FRAME_OPTIONS='SAMEORIGIN' # only if django version >= 3.0

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'homodaba.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'homodaba.wsgi.application'

# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases

# Por defecto sqlite3
SQLITE_ROOT = Path(os.getenv("SQLITE_ROOT", "")) if os.getenv("SQLITE_ROOT", "") else BASE_DIR

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': SQLITE_ROOT / 'db.sqlite3',
    }
}

# Opcion de mysql
if os.getenv('DATABASE_ENGINE', '') == 'mysql':
    DATABASES = {
        'default':{
            'ENGINE': 'django.db.backends.mysql',
            'NAME': os.getenv('DATABASE_NAME', 'dbtest'),
            'USER': os.getenv('DATABASE_USER', 'dbroot'),
            'PASSWORD':  os.getenv('DATABASE_PASSWORD', 'dbpass.123'),
            'HOST': os.getenv('DATABASE_HOST', ''),
            'PORT': '',
        }
    }




# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/3.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/

# STATIC_URL = '/static/'

STATIC_ROOT = os.getenv('STATIC_ROOT', BASE_DIR / '../static')

# Variable para mapear la app dentro de un directorio (para el reverse proxy)
# Por ejemplo, para publicar detras de un proxy en https://example.com/homodaba
# HOME_URL_PATH = 'homodaba/'
HOME_URL_PATH = os.getenv('HOME_URL_PATH', '')

# Variable para definir donde se sirven los estaticos, esto es util para 
# servir estaticos en un reverse proxy que apunte a un contenedor docker
STATIC_URL = os.getenv('STATIC_URL', '/%sstatic/' % HOME_URL_PATH)

# Por ahora no usamos uploads, pero en un futuro... who knows!
# MEDIA_URL = '/%supload/' % HOME_URL_PATH
