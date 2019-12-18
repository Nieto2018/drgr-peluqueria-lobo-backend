"""
Django settings for backend project.

Generated by 'django-admin startproject' using Django 2.1.5.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.1/ref/settings/
"""

import datetime
import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'ae6ipj5p05co-&zv16xq$$#pzg9((nbi5+(gq^lr_u59qt6w-5'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

# Application definition

DJANGO_APPS = [
    # Default Django apps:
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Admin
    'django.contrib.admin'
]

THIRD_PARTY_APPS = [
    'graphene_django',
    # To adds CORS (Cross-Origin Resource Sharing) headers to responses (Frontend)
    'corsheaders',

    # For subscriptions
    'channels',
]

LOCAL_APPS = [
    'dates'
]

INSTALLED_APPS = THIRD_PARTY_APPS + LOCAL_APPS + DJANGO_APPS

# Define a custom User model
AUTH_USER_MODEL = 'dates.User'

# Graphene settings
GRAPHENE = {
    'SCHEMA': 'backend.schema.graphql_schema',
    'MIDDLEWARE': [
        # Django GraphQL JWT
        'graphql_jwt.middleware.JSONWebTokenMiddleware',
    ],
}

# Django GraphQL JWT settings
GRAPHQL_JWT = {
    'JWT_VERIFY_EXPIRATION': True,
    'JWT_EXPIRATION_DELTA': datetime.timedelta(minutes=30),  # Default minutes=5
}

AUTHENTICATION_BACKENDS = [
    # Django administration
    'django.contrib.auth.backends.ModelBackend',

    # Django GraphQL JWT
    'graphql_jwt.backends.JSONWebTokenBackend',
]

# Channels settings
# In this simple example we use in-process in-memory Channel layer.
# In a real-life cases you should use Redis or something familiar.
CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}
ROOT_URLCONF = 'backend.urls'
ASGI_APPLICATION = "backend.routing.application"

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    # To adds CORS (Cross-Origin Resource Sharing) headers to responses (Frontend)
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# To adds CORS (Cross-Origin Resource Sharing) headers to responses (Frontend)
CORS_ORIGIN_ALLOW_ALL = True
# CORS_ORIGIN_WHITELIST = [
#     'http://localhost:3000',
#     'http://127.0.0.1:3000'
# ]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'backend/templates'),
        ],
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

WSGI_APPLICATION = 'backend.wsgi.application'

# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Password validation
# https://docs.djangoproject.com/en/2.1/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/2.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.1/howto/static-files/

STATIC_URL = '/static/'

# It is compulsory in order to avoid the [Errno 111] when the Rest
# API is called to reset password by Email
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST: 'localhost'
# EMAIL_PORT: 1025


#########################################################################################################
#########################################################################################################
# Constants
#########################################################################################################
#########################################################################################################

##########################
# Config constants
##########################

CLIENT_URL = 'http://localhost:3000'
SITE_NAME = 'Peluquería Lobo'

##########################
#  Users
##########################

# TODO delete comment constants?
# Messages
# EMAIL_SENT = 'EmailSent'
# EMAIL_UPDATED = 'EmailUpdated'
# PASSWORD_RESET = 'PasswordReset'
# USER_ACTIVATED = 'UserActivated'
# USER_DEACTIVATED = 'UserDeactivated'

# Error messages
USER_DOES_NOT_EXIST_ERROR = 'UserDoesNotExistError'
USER_NOT_LOGGED_IN_ERROR = 'UserNotLoggedInError'
# USER_NOT_ACTIVATED_ERROR = 'UserNotActivatedError'
USER_ACTIVE_ERROR = 'UserActiveErrorError'
USER_INACTIVE_ERROR = 'UserInactiveError'
# USER_ACTIVATED_ERROR = 'UserActivated'
# USER_DEACTIVATED_ERROR = 'UserDeactivatedError'
# EMAIL_NOT_SENT_ERROR = 'EmailNotSendError'
NAME_REQUIRED_ERROR = 'NameRequiredError'
SURNAMES_REQUIRED_ERROR = 'SurnamesRequiredError'
EMAIL_REQUIRED_ERROR = 'EmailRequiredError'
EMAIL_ALREADY_REGISTERED_ERROR = 'EmailAlreadyRegisteredError'
# EMAIL_NOT_UPDATED_ERROR = 'EmailNotUpdatedError'
# PASSWORD_NOT_RESET_ERROR = 'PasswordNotResetError'
PASSWORD1_REQUIRED_ERROR = 'Password1RequiredError'
PASSWORD2_REQUIRED_ERROR = 'Password2RequiredError'
PASSWORDS_NOT_MATCH_ERROR = 'PasswordsNotMatchError'
##########################
# Generics
##########################

# Messages
OK = 'OK'
KO = 'KO'

# Error messages
INVALID_ACTION_ERROR = 'InvalidActionError'
TOKEN_ERROR = 'TokenError'
TOKEN_REQUIRED_ERROR = 'TokenRequiredError'
TOKEN_USED_ERROR = 'TokenUsedError'
TOKEN_NOT_MATCH_ERROR = 'TokenNotMatchError'
EXPIRED_TOKEN_ERROR = 'ExpiredTokenError'
