from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-s!q(iv&-_9p_23vma$o*br1h)4ycfj50u(5i7lukbew*3vdqc)"

# SECURITY WARNING: define the correct hosts in production!
ALLOWED_HOSTS = ["*"]

# EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'anam.meteo@gmail.com'
EMAIL_HOST_PASSWORD = 'kedg mzai tkhr fjlk'
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER #'ANAM <anaslcnm.meteo@gmail.com>'

try:
    from .local import *
except ImportError:
    pass
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,

    'formatters': {
        'default': {
            'format': '[{asctime}] {levelname} {name} {message}',
            'style': '{',
        },
    },

    'handlers': {
        'info_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/info.log'),
            'maxBytes': 5 * 1024 * 1024,
            'backupCount': 3,
            'formatter': 'default',
            'encoding': 'utf8',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/error.log'),
            'maxBytes': 5 * 1024 * 1024,
            'backupCount': 3,
            'formatter': 'default',
            'encoding': 'utf8',
        },
        'critical_file': {
            'level': 'CRITICAL',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/critical.log'),
            'maxBytes': 5 * 1024 * 1024,
            'backupCount': 3,
            'formatter': 'default',
            'encoding': 'utf8',
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'default',
        },
    },

    'loggers': {
        'django': {
            'handlers': ['info_file', 'error_file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['error_file', 'console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['critical_file'],
            'level': 'CRITICAL',
            'propagate': False,
        },
    }
}


CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_BACKEND = 'django-db'

# Pour les tâches périodiques
INSTALLED_APPS += [
    'django_celery_beat',
    'django_celery_results',
]

# Timezone pour les tâches
CELERY_TIMEZONE = 'Africa/Ouagadougou'
