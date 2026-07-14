"""
Django settings for cimetiere_api project.
CORRECTIONS :
  - load_dotenv avec override=True pour forcer la lecture du .env
  - DB forcé en PostgreSQL (suppression du fallback sqlite3)
  - EMAIL_HOST_USER et PASSWORD lus depuis .env avec override
  - LANGUAGE_CODE et TIME_ZONE en français/Brazzaville
  - corsheaders ajouté pour le frontend Flet
"""
import os
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url
BASE_DIR = Path(__file__).resolve().parent.parent

# override=True : force la lecture du .env même si les variables sont déjà dans l'environnement
load_dotenv(BASE_DIR / '.env', override=True)

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-change-moi')
DEBUG = os.getenv('DEBUG', 'True').lower() in ('1', 'true', 'yes')
allowed_hosts = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
ALLOWED_HOSTS = list(dict.fromkeys([host.strip() for host in allowed_hosts if host.strip()] + ['localhost', '127.0.0.1', 'testserver']))
USE_SQLITE = os.getenv('USE_SQLITE', 'True').lower() in ('1', 'true', 'yes')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'cimetiere',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # doit être en premier
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

CORS_ALLOWED_ORIGINS = [
    "http://localhost:8550",
    "http://127.0.0.1:8550",
]
CORS_ALLOW_ALL_ORIGINS = True  # en dev

ROOT_URLCONF = 'cimetiere_api.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'cimetiere_api.wsgi.application'

# ─── Base de données PostgreSQL ───────────────────────────────────────────────
# Nom de la base : cimetiere_gi2
# Créer avec : psql -U postgres -c "CREATE DATABASE cimetiere_gi2;"
if USE_SQLITE:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL'),
        conn_max_age=600,
        conn_health_checks=True,
    )
        }
    

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Africa/Brazzaville'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ─── Email configuration ──────────────────────────────────────────────────────
# Le code MFA est envoyé VERS l'email du client (pas vers l'admin).
# En développement (`DEBUG=True`) on utilise le backend console pour éviter
# d'envoyer de vrais emails (préserve les mots de passe et codes).
if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

EMAIL_HOST        = os.getenv('EMAIL_HOST',        'smtp.gmail.com')
EMAIL_PORT        = int(os.getenv('EMAIL_PORT',    587))
EMAIL_USE_TLS     = os.getenv('EMAIL_USE_TLS', 'True').lower() in ('1', 'true', 'yes')
EMAIL_HOST_USER   = os.getenv('EMAIL_HOST_USER',   '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL  = os.getenv(
    'DEFAULT_FROM_EMAIL',
    f"Gestion Cimetière <{EMAIL_HOST_USER}>"
)

EMAIL_TIMEOUT         = int(os.getenv('EMAIL_TIMEOUT',         20))
EMAIL_SEND_RETRIES    = int(os.getenv('EMAIL_SEND_RETRIES',     3))
EMAIL_BACKOFF_SECONDS = int(os.getenv('EMAIL_BACKOFF_SECONDS',  1))