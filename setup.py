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
        'django-cms==3.1.4',
        'django-reversion',

        'djangocms-admin-style<1.0.0',
        # common
        # TODO: mostly to be split out into other packages
        'django-compressor',
        'YURL',
        'South',
        'requests',
        'Pillow',
        'lxml',
        'django-treebeard',
        'django-simple-captcha',
        'BeautifulSoup4',
        'django-parler',
        'django-robots',
        'aldryn-boilerplates',
        'django-filer',
        # hvad >= 1.x introduced newer internal apis
        # aldryn packages have not been upgraded
        # to support these changes
        'django-hvad<1.0.0',
        'aldryn-snake',

        # default plugins
        # TODO: split into other packages
        'djangocms-googlemap',
        'djangocms-link',
        'djangocms-snippet',
        'djangocms-text-ckeditor<2.8',
        'cmsplugin-filer',

        # djangocms-link installs Django-Select2. But Django-Select2 v5 does not
        # support Django 1.6.x anymore
        'django-select2<5',
    ),
    include_package_data=True,
    zip_safe=False,
)
