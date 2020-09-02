#languages.py
import addonHandler
addonHandler.initTranslation()

from languageHandler import getLanguageDescription
from locale import getdefaultlocale


class Language(object):

    def __init__(self, code, langNames):
        self.lang = code
        self.names = langNames

    @property
    def code(self):
        return self.lang

    @property
    def name(self):
        name = getLanguageDescription(self.lang)
        if not name:
            name = self.names.get(self.lang, None)
        return name if name else self.lang


class Languages(object):

    def __init__(self, availableLanguages, langNames):
        self.langs = availableLanguages
        self.names = langNames

    def fromList(self):
        for lang in list({c.split('-')[0]: c for c in self.langs}):
            yield Language(lang, self.names)

    def intoList(self, lng):
        if not lng: return []
        for lang in self.langs:
            l = lang.split('-')
            if l[0]==lng:
                yield Language(l[1], self.names)

    def isAvailable(self, source, target):
        return "%s-%s" % (source, target) in self.langs

    @property
    def defaultFrom(self):
        return 'en' if next(filter(lambda l: l.code=='en', self.fromList()), None) else self.langs[0].split('-')[0]

    @property
    def defaultInto(self):
        localeLang = getdefaultlocale()[0].split('_')[0]
        return localeLang if next(filter(lambda l: l.code==localeLang, self.intoList(self.defaultFrom)), None) else [l for l in self.intoList(self.defaultFrom)][0].code

    def __getitem__(self, lang):
        return Language(lang, self.names)


langNames = {
    # Translators: The name of the language, which may not be in the main list
    "ceb":_("Cebuano"),
    # Translators: The name of the language, which may not be in the main list
    "eo":_("Esperanto"),
    # Translators: The name of the language, which may not be in the main list
    "hmn":_("Hmong"),
    # Translators: The name of the language, which may not be in the main list
    "ht":_("Creole Haiti"),
    # Translators: The name of the language, which may not be in the main list
    "jv":_("Javanese"),
    # Translators: The name of the language, which may not be in the main list
    "la":_("Latin"),
    # Translators: The name of the language, which may not be in the main list
    "mg":_("Malagasy"),
    # Translators: The name of the language, which may not be in the main list
    "mhr":_("Meadow Mari"),
    # Translators: The name of the language, which may not be in the main list
    "mrj":_("Hill Mari"),
    # Translators: The name of the language, which may not be in the main list
    "my":_("Myanmar (Burmese)"),
    # Translators: The name of the language, which may not be in the main list
    "ny":_("Chichewa"),
    # Translators: The name of the language, which may not be in the main list
    "so":_("Somali"),
    # Translators: The name of the language, which may not be in the main list
    "st":_("Sesotho"),
    # Translators: The name of the language, which may not be in the main list
    "su":_("Sundanese"),
    # Translators: The name of the language, which may not be in the main list
    "tl":_("Tagalog"),
    # Translators: The name of the language, which may not be in the main list
    "yi":_("Yiddish"),
}

availableLanguages = [
    "be-be",
    "be-ru",
    "bg-ru",
    "cs-cs",
    "cs-en",
    "cs-ru",
    "da-en",
    "da-ru",
    "de-de",
    "de-en",
    "de-ru",
    "de-tr",
    "el-en",
    "el-ru",
    "en-cs",
    "en-da",
    "en-de",
    "en-el",
    "en-en",
    "en-es",
    "en-et",
    "en-fi",
    "en-fr",
    "en-it",
    "en-lt",
    "en-lv",
    "en-nl",
    "en-no",
    "en-pt",
    "en-ru",
    "en-sk",
    "en-sv",
    "en-tr",
    "en-uk",
    "es-en",
    "es-es",
    "es-ru",
    "et-en",
    "et-ru",
    "fi-en",
    "fi-ru",
    "fi-fi",
    "fr-fr",
    "fr-en",
    "fr-ru",
    "hu-hu",
    "hu-ru",
    "it-en",
    "it-it",
    "it-ru",
    "lt-en",
    "lt-lt",
    "lt-ru",
    "lv-en",
    "lv-ru",
    "mhr-ru",
    "mrj-ru",
    "nl-en",
    "nl-ru",
    "no-en",
    "no-ru",
    "pl-ru",
    "pt-en",
    "pt-ru",
    "ru-be",
    "ru-bg",
    "ru-cs",
    "ru-da",
    "ru-de",
    "ru-el",
    "ru-en",
    "ru-es",
    "ru-et",
    "ru-fi",
    "ru-fr",
    "ru-hu",
    "ru-it",
    "ru-lt",
    "ru-lv",
    "ru-mhr",
    "ru-mrj",
    "ru-nl",
    "ru-no",
    "ru-pl",
    "ru-pt",
    "ru-ru",
    "ru-sk",
    "ru-sv",
    "ru-tr",
    "ru-tt",
    "ru-uk",
    "ru-zh",
    "sk-en",
    "sk-ru",
    "sv-en",
    "sv-ru",
    "tr-de",
    "tr-en",
    "tr-ru",
    "tt-ru",
    "uk-en",
    "uk-ru",
    "uk-uk",
    "zh-ru"
]

langs = Languages(availableLanguages, langNames)
