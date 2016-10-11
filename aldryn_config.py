# -*- coding: utf-8 -*-
import json
import os

from distutils.version import LooseVersion

from aldryn_client import forms

SYSTEM_FIELD_WARNING = 'WARNING: this field is auto-written. Please do not change it here.'


class Form(forms.BaseForm):
    unescaped_render_model_tags = forms.CheckboxField(
        'Leave "render_model" tags unescaped? (security risk)',
        required=False,
        initial=True,
        help_text=(
            'IMPORTANT: Please review your project templates before un-checking this box. '  # noqa
            'See: http://www.django-cms.org/en/blog/2016/04/26/security-updates-django-cms-released/.'  # noqa
        ),
    )
    permissions_enabled = forms.CheckboxField(
        'Enable permission checks',
        required=False,
        initial=True,
        help_text=(
            'When set, provides new fields in each page\'s settings to assign '
            'levels of access to particular users.'
        ),
    )
    cms_templates = forms.CharField(
        'CMS Templates',
        required=True,
        initial='[["default.html", "Default"]]',
        help_text=SYSTEM_FIELD_WARNING,
    )
    boilerplate_name = forms.CharField(
        'Boilerplate Name',
        required=False,
        initial='',
        help_text=SYSTEM_FIELD_WARNING,
    )
    cms_content_cache_duration = forms.NumberField(
        'Set Cache Duration for Content',
        required=False,
        initial=60,
        help_text=(
            'Cache expiration (in seconds) for show_placeholder, page_url, '
            'placeholder and static_placeholder template tags.'
        ),
    )
    cms_menus_cache_duration = forms.NumberField(
        'Set Cache Duration for Menus',
        required=False,
        initial=3600,
        help_text='Cache expiration (in seconds) for the menu tree.',
    )

    def to_settings(self, data, settings):
        from functools import partial
        import django
        from django.core.urlresolvers import reverse_lazy
        from aldryn_addons.utils import boolean_ish, djsenv
        from aldryn_django import storage

        env = partial(djsenv, settings=settings)

        django_version = LooseVersion(django.get_version())

        is_django_18_or_later = django_version >= LooseVersion('1.8')
        is_django_19_or_later = django_version >= LooseVersion('1.9')

        # Core CMS stuff
        settings['INSTALLED_APPS'].extend([
            'cms',
            # 'aldryn_django_cms' must be after 'cms', otherwise we get
            # import time exceptions on other packages (e.g alryn-bootstrap3
            # returns:
            # link_page = cms.models.fields.PageField(
            # AttributeError: 'module' object has no attribute 'fields'
            # )
            'aldryn_django_cms',
            'menus',
            'sekizai',
            'treebeard',
            'reversion',
        ])

        # TODO: break out this stuff into other addons
        settings['INSTALLED_APPS'].extend([
            'parler',
        ])
        settings['INSTALLED_APPS'].insert(
            settings['INSTALLED_APPS'].index('django.contrib.admin'),
            'djangocms_admin_style',
        )

        if is_django_18_or_later:
            settings['TEMPLATES'][0]['OPTIONS']['context_processors'].extend([
                'sekizai.context_processors.sekizai',
                'cms.context_processors.cms_settings',
            ])
        else:
            settings['TEMPLATE_CONTEXT_PROCESSORS'].extend([
                'sekizai.context_processors.sekizai',
                'cms.context_processors.cms_settings',
            ])

        settings['MIDDLEWARE_CLASSES'].extend([
            'cms.middleware.user.CurrentUserMiddleware',
            'cms.middleware.page.CurrentPageMiddleware',
            'cms.middleware.toolbar.ToolbarMiddleware',
            'cms.middleware.language.LanguageCookieMiddleware',
        ])
        settings['MIDDLEWARE_CLASSES'].insert(0, 'cms.middleware.utils.ApphookReloadMiddleware',)

        settings['ADDON_URLS_I18N_LAST'] = 'cms.urls'

        settings['CMS_PERMISSION'] = data['permissions_enabled']

        cache_durations = settings.setdefault('CMS_CACHE_DURATIONS', {
            'content': 60,
            'menus': 60 * 60,
            'permissions': 60 * 60,
        })

        if data['cms_content_cache_duration']:
            cache_durations['content'] = data['cms_content_cache_duration']

        if data['cms_menus_cache_duration']:
            cache_durations['menus'] = data['cms_menus_cache_duration']

        old_cms_templates_json = os.path.join(settings['BASE_DIR'], 'cms_templates.json')

        if os.path.exists(old_cms_templates_json):
            # Backwards compatibility with v2
            with open(old_cms_templates_json) as fobj:
                templates = json.load(fobj)
        else:
            templates= settings.get('CMS_TEMPLATES', json.loads(data['cms_templates']))

        settings['CMS_TEMPLATES'] = templates

        # languages
        language_codes = [code for code, lang in settings['LANGUAGES']]
        settings['CMS_LANGUAGES'] = {
            'default': {
                'fallbacks': [fbcode for fbcode in language_codes],
                'redirect_on_fallback': True,
                'public': True,
                'hide_untranslated': False,
            },
            1: [
                {
                    'code': code,
                    'name': settings['ALL_LANGUAGES_DICT'][code],
                    'fallbacks': [fbcode for fbcode in language_codes if fbcode != code],
                    'public': True
                } for code in language_codes
            ]
        }

        settings['PARLER_LANGUAGES'] = {}

        for site_id, languages in settings['CMS_LANGUAGES'].items():
            if isinstance(site_id, int):
                langs = [
                    {
                        'code': lang['code'],
                        'fallbacks': [fbcode for fbcode in language_codes if fbcode != lang['code']]
                    } for lang in languages
                ]
                settings['PARLER_LANGUAGES'].update({site_id: langs})

        parler_defaults = {'fallback': settings['LANGUAGE_CODE']}

        for k, v in settings['CMS_LANGUAGES'].get('default', {}).items():
            if k in ['hide_untranslated', ]:
                parler_defaults.update({k: v})

        settings['PARLER_LANGUAGES'].update({'default': parler_defaults})

        # aldryn-boilerplates and aldryn-snake

        # FIXME: Make ALDRYN_BOILERPLATE_NAME a configurable parameter

        settings['ALDRYN_BOILERPLATE_NAME'] = env(
            'ALDRYN_BOILERPLATE_NAME',
            data.get('boilerplate_name', 'legacy'),
        )
        settings['INSTALLED_APPS'].append('aldryn_boilerplates')

        if is_django_18_or_later:
            TEMPLATE_CONTEXT_PROCESSORS = settings['TEMPLATES'][0]['OPTIONS']['context_processors']
            TEMPLATE_LOADERS = settings['TEMPLATES'][0]['OPTIONS']['loaders']
        else:
            TEMPLATE_CONTEXT_PROCESSORS = settings['TEMPLATE_CONTEXT_PROCESSORS']
            TEMPLATE_LOADERS = settings['TEMPLATE_LOADERS']
        TEMPLATE_CONTEXT_PROCESSORS.extend([
            'aldryn_boilerplates.context_processors.boilerplate',
            'aldryn_snake.template_api.template_processor',
        ])
        TEMPLATE_LOADERS.insert(
            TEMPLATE_LOADERS.index(
                'django.template.loaders.app_directories.Loader'),
            'aldryn_boilerplates.template_loaders.AppDirectoriesLoader'
        )

        settings['STATICFILES_FINDERS'].insert(
            settings['STATICFILES_FINDERS'].index('django.contrib.staticfiles.finders.AppDirectoriesFinder'),
            'aldryn_boilerplates.staticfile_finders.AppDirectoriesFinder',
        )

        # django sitemap support
        settings['INSTALLED_APPS'].append('django.contrib.sitemaps')

        # django-compressor
        settings['INSTALLED_APPS'].append('compressor')
        settings['STATICFILES_FINDERS'].append('compressor.finders.CompressorFinder')
        # Disable django-comporessor for now. It does not work with the current
        # setup. The cache is shared, which holds the manifest. But the
        # compressed files reside in the docker container, which can go away at
        # any time.
        # Working solutions could be:
        # 1) use pre-compression
        # (https://django-compressor.readthedocs.org/en/latest/usage/#pre-compression)
        # at docker image build time.
        # 2) Use shared storage and save the manifest with the generated files.
        # Although that could be a problem if different versions of the same
        # app compete for the manifest file.

        # We're keeping compressor in INSTALLED_APPS for now, so that templates
        # in existing projects don't break.
        settings['COMPRESS_ENABLED'] = env('COMPRESS_ENABLED', False)

        if settings['COMPRESS_ENABLED']:
            # Set far-future expiration headers for django-compressor
            # generated files.
            settings.setdefault('STATIC_HEADERS', []).insert(0, (
                r'{}/.*'.format(settings.get('COMPRESS_OUTPUT_DIR', 'CACHE')),
                {
                    'Cache-Control': 'public, max-age={}'.format(86400 * 365),
                },
            ))

        # django-robots
        settings['INSTALLED_APPS'].append('robots')

        # django-filer
        settings['INSTALLED_APPS'].extend([
            'filer',
            'easy_thumbnails',
            'mptt',
            'polymorphic',
        ])
        settings['FILER_DEBUG'] = boolean_ish(env('FILER_DEBUG', settings['DEBUG']))
        settings['FILER_ENABLE_LOGGING'] = boolean_ish(env('FILER_ENABLE_LOGGING', True))
        settings['FILER_IMAGE_USE_ICON'] = True
        settings['ADDON_URLS'].append(
            'filer.server.urls'
        )
        settings.setdefault('MEDIA_HEADERS', []).insert(0, (
            r'filer_public(?:_thumbnails)?/.*',
            {
                'Cache-Control': 'public, max-age={}'.format(86400 * 365),
            },
        ))

        # easy-thumbnails
        settings['INSTALLED_APPS'].extend([
            'easy_thumbnails',
        ])
        settings['THUMBNAIL_QUALITY'] = env('THUMBNAIL_QUALITY', 90)
        # FIXME: enabling THUMBNAIL_HIGH_RESOLUTION causes timeouts/500!
        settings['THUMBNAIL_HIGH_RESOLUTION'] = False
        settings['THUMBNAIL_PRESERVE_EXTENSIONS'] = ['png', 'gif']
        settings['THUMBNAIL_PROCESSORS'] = (
            'easy_thumbnails.processors.colorspace',
            'easy_thumbnails.processors.autocrop',
            'filer.thumbnail_processors.scale_and_crop_with_subject_location',
            'easy_thumbnails.processors.filters',
        )
        settings['THUMBNAIL_SOURCE_GENERATORS'] = (
            'easy_thumbnails.source_generators.pil_image',
        )
        settings['THUMBNAIL_CACHE_DIMENSIONS'] = True

        # easy_thumbnails uses django's default storage backend (local file
        # system storage) by default, even if the DEFAULT_FILE_STORAGE setting
        # points to something else.
        # If the DEFAULT_FILE_STORAGE has been set to a value known by
        # aldryn-django, then use that as THUMBNAIL_DEFAULT_STORAGE as well.
        for storage_backend in storage.SCHEMES.values():
            if storage_backend == settings['DEFAULT_FILE_STORAGE']:
                settings['THUMBNAIL_DEFAULT_STORAGE'] = storage_backend
                break

        settings['MIGRATION_COMMANDS'].append(
            'python manage.py cms fix-tree'
        )

        # default plugins
        settings['INSTALLED_APPS'].extend([
            'djangocms_text_ckeditor',
            'djangocms_link',
            'djangocms_snippet',
            'djangocms_googlemap',
            # cmsplugin-filer
            'cmsplugin_filer_file',
            'cmsplugin_filer_image',

            # required by aldryn-forms
            'captcha',
        ])

        # boilerplate must provide /static/js/modules/ckeditor.wysiwyg.js and /static/css/base.css
        CKEDITOR_SETTINGS = {
            'height': 300,
            'language': '{{ language }}',
            'toolbar': 'CMS',
            'skin': 'moono',
            'extraPlugins': 'cmsplugins',
            'toolbar_HTMLField': [
                ['Undo', 'Redo'],
                ['cmsplugins', '-', 'ShowBlocks'],
                ['Format', 'Styles'],
                ['TextColor', 'BGColor', '-', 'PasteText', 'PasteFromWord'],
                ['Maximize', ''],
                '/',
                ['Bold', 'Italic', 'Underline', '-', 'Subscript', 'Superscript', '-', 'RemoveFormat'],
                ['JustifyLeft', 'JustifyCenter', 'JustifyRight'],
                ['HorizontalRule'],
                ['Link', 'Unlink'],
                ['NumberedList', 'BulletedList', '-', 'Outdent', 'Indent', '-', 'Table'],
                ['Source'],
                ['Link', 'Unlink', 'Anchor'],
            ],
        }
        boilerplate_name = settings['ALDRYN_BOILERPLATE_NAME']
        if boilerplate_name == 'bootstrap3':
            CKEDITOR_SETTINGS['stylesSet'] = 'default:/static/js/addons/ckeditor.wysiwyg.js'
            CKEDITOR_SETTINGS['contentsCss'] = ['/static/css/base.css']
        else:
            CKEDITOR_SETTINGS['stylesSet'] = 'default:/static/js/modules/ckeditor.wysiwyg.js'
            CKEDITOR_SETTINGS['contentsCss'] = ['/static/css/base.css']

        # select2 (required by djangocms_link plugin)
        settings['INSTALLED_APPS'].extend([
            'django_select2',
        ])

        # django-select2 < 5 is not compatible with Django >= 1.9
        # so only enable select2 if we're on Django <= 1.8
        settings['DJANGOCMS_LINK_USE_SELECT2'] = not is_django_19_or_later

        settings['ADDON_URLS'].append('aldryn_django_cms.urls')
        settings['ADDON_URLS_I18N'].append('aldryn_django_cms.urls_i18n')

        if 'ALDRYN_SSO_LOGIN_WHITE_LIST' in settings:
            # stage sso enabled
            # add internal endpoints that do not require authentication
            settings['ALDRYN_SSO_LOGIN_WHITE_LIST'].append(reverse_lazy('cms-check-uninstall'))
            # this is an internal django-cms url
            # which gets called when a user logs out from toolbar
            settings['ALDRYN_SSO_LOGIN_WHITE_LIST'].append(reverse_lazy('admin:cms_page_resolve'))

        # This may need to be removed in a future release.
        settings['CMS_UNESCAPED_RENDER_MODEL_TAGS'] = data['unescaped_render_model_tags']

        # Prevent injecting random comments to counter BREACH/CRIME attacks
        # into the page tree snippets, as the javascript parsing the result
        # expects a single top-level element.
        (settings
         .setdefault('RANDOM_COMMENT_EXCLUDED_VIEWS', set([]))
         .add('cms.admin.pageadmin.get_tree'))

        return settings
