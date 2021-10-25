#!/usr/bin/env python
import os
import sys

import django
from django.conf import settings
from django.core.management import call_command


def runtests():
    if not settings.configured:
        # Choose database for settings
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:'
            }
        }

        # Configure test environment
        settings.configure(
            DATABASES=DATABASES,
            INSTALLED_APPS=[
                'django.contrib.admin',
                'django.contrib.auth',
                'django.contrib.contenttypes',
                'django.contrib.sessions',
                'django.contrib.messages',
                'django.contrib.staticfiles',
                'privacydates'
            ],
            MIDDLEWARE=[
                'django.middleware.security.SecurityMiddleware',
                'django.contrib.sessions.middleware.SessionMiddleware',
                'django.middleware.common.CommonMiddleware',
                'django.middleware.csrf.CsrfViewMiddleware',
                'django.contrib.auth.middleware.AuthenticationMiddleware',
                'django.contrib.messages.middleware.MessageMiddleware',
                'django.middleware.clickjacking.XFrameOptionsMiddleware',
            ],
            ROOT_URLCONF='',  # tests override urlconf, but it still needs to be defined
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
            ],
            SECRET_KEY='!f!&e7juvx_3fin+=n23wuy*7)oomvpno_)0zypv+8c1%isw(^',
        )

    if django.VERSION >= (1, 7):
        django.setup()
    failures = call_command(
        'test', 'privacydates', interactive=False, failfast=False, verbosity=2)

    sys.exit(bool(failures))


if __name__ == '__main__':
    runtests()
