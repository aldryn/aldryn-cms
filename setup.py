# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
from aldryn_django_cms import __version__

setup(
    name="aldryn-django-cms",
    version=__version__,
    description='An opinionated django CMS setup bundled as an Aldryn Addon',
    author='Divio AG',
    author_email='info@divio.ch',
    url='https://github.com/aldryn/aldryn-django-cms',
    packages=find_packages(),
    install_requires=(
        'aldryn-addons',
        'django-cms==4.0.0dev11',
        'requests',

        # NOTE: django-cms doesn't require this, but many of the addons do.
        'django-treebeard>=4.0.1',         # django-cms
        'djangocms-admin-style',           # django-cms
        'django-select2>=4.3',

        # Other common
        # ------------
        # TODO: mostly to be split out into other packages
        'aldryn-boilerplates>=0.7.4',
        'aldryn-snake',
        'django-compressor',
        'django-parler',
        # Django Sortedm2m 1.3 introduced a regression, that was fixed in 1.3.2
        # See https://github.com/gregmuellegger/django-sortedm2m/issues/80
        'django-sortedm2m>=1.2.2,!=1.3.0,!=1.3.1',
        'django-robots',
        'django-simple-captcha',
        'lxml',
        'YURL',
        'psycopg2<2.8',
    ),
    include_package_data=True,
    zip_safe=False,
)
