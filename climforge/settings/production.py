from .base import *

DEBUG = False
ALLOWED_HOSTS = ['*']
SECRET_KEY = '+o&0%yx@2!4ym0*a0!$6j=jf-w528b=q%&wo%*@#g9)c!x3y#p'
try:
    from .local import *
except ImportError:
    pass
import os
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

