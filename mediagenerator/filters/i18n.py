from django.conf import settings
from django.http import HttpRequest
from django.views.i18n import javascript_catalog
from hashlib import sha1
from mediagenerator.generators.bundles.base import Filter

if settings.USE_I18N:
    LANGUAGES = [code for code, _ in settings.LANGUAGES]
else:
    LANGUAGES = (settings.LANGUAGE_CODE,)

class I18N(Filter):
    takes_input = False

    def __init__(self, **kwargs):
        super(I18N, self).__init__(**kwargs)
        assert self.filetype == 'js', (
            'I18N only supports compilation to js. '
            'The parent filter expects "%s".' % self.filetype)

    def get_variations(self):
        return {'language': LANGUAGES}

    def get_output(self, variation):
        language = variation['language']
        yield self._generate(language)

    def get_dev_output(self, name, variation):
        language = variation['language']
        assert language == name + '.js'
        return self._generate(language)

    def get_dev_output_names(self, variation):
        language = variation['language']
        content = self._generate(language)
        hash = sha1(content).hexdigest()
        yield content, hash

    def _generate(self, language):
        language_bidi = language.split('-')[0] in settings.LANGUAGES_BIDI
        request = HttpRequest()
        request.GET['language'] = language
        # Add some JavaScript data
        content = 'var LANGUAGE_CODE = "%s";\n' % language
        content += 'var LANGUAGE_BIDI = ' + \
            (language_bidi and 'true' or 'false') + ';\n'
        content += javascript_catalog(request,
            packages=settings.INSTALLED_APPS).content
        # The hgettext() function just calls gettext() internally, but
        # it won't get indexed by makemessages.
        content += '\nwindow.hgettext = function(text) { return gettext(text); };\n'
        # Add a similar hngettext() function
        content += 'window.hngettext = function(singular, plural, count) { return ngettext(singular, plural, count); };\n'
        return content
