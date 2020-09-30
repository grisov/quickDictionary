#languages.py
import addonHandler
from logHandler import log
try:
	addonHandler.initTranslation()
except addonHandler.AddonError:
	log.warning("Unable to initialise translations. This may be because the addon is running from NVDA scratchpad.")

from languageHandler import getLanguageDescription
from locale import getdefaultlocale


class Language(object):
	"""Object representation of language"""

	def __init__(self, code:str, langNames:dict):
		"""Language object fields initialization.
		@param code: usually two-character language code
		@type code: str
		@param langNames: additional languages, where key is a two-character code and value is name of the language
		@type langNames: dict
		"""
		self.lang = code
		self.names = langNames

	@property
	def code(self) -> str:
		"""Language code.
		@return: usually two-character language code
		@rtype: str
		"""
		return self.lang

	@property
	def name(self) -> str:
		"""Language name.
		@return: full language name
		@rtype: str
		"""
		name = getLanguageDescription(self.lang)
		if not name:
			name = self.names.get(self.lang, None)
		return name or self.lang


class Languages(object):
	"""Represents a list of languages available in the dictionary service."""

	def __init__(self, availableLanguages:list, langNames:dict):
		"""Initialization of an object representing a list of available language pairs.
		@param availableLanguages: list of language pairs available in the dictionary
		@type availableLanguages: list
		@param langNames: additional languages, where key is a two-character code and value is name of the language
		@type langNames: dict
		"""
		self.langs = availableLanguages
		self.names = langNames

	def fromList(self) -> list:
		"""Sequence of available source languages.
		@return: sequence of available source languages
		@rtype: list of Language
		"""
		for lang in list({c.split('-')[0]: c for c in self.langs}):
			yield Language(lang, self.names)

	def intoList(self, lng: str) -> list:
		"""Sequence of available target languages for a given source language.
		@param lng: source language code
		@type lng: str
		@return: sequence of available target languages
		@rtype: list of Language
		"""
		if not lng: return []
		for lang in self.langs:
			l = lang.split('-')
			if l[0]==lng:
				yield Language(l[1], self.names)

	def isAvailable(self, source: str, target: str) -> bool:
		"""Indicates whether the selected language pair is in the list of available languages.
		@param source: source language code
		@type source: str
		@param target: target language code
		@type target: str
		@return: whether a language pair is present in the list of available
		@rtype: bool
		"""
		return "%s-%s" % (source, target) in self.langs

	@property
	def defaultFrom(self) -> str:
		"""Default source language.
		@return: 'en' if available, else - the first language in list of source languages
		@rtype: str
		"""
		return 'en' if next(filter(lambda l: l.code=='en', self.fromList()), None) else self.langs[0].split('-')[0]

	@property
	def defaultInto(self) -> str:
		"""Default target language.
		@return: locale language, if it is available as the target for the default source, otherwise the first one in the list
		@rtype: str
		"""
		return self.locale if next(filter(lambda l: l.code==self.locale, self.intoList(self.defaultFrom)), None) else [l for l in self.intoList(self.defaultFrom)][0].code

	@property
	def locale(self) -> str:
		"""User locale language.
		@return: locale language code used on the user's computer
		@rtype: str
		"""
		return getdefaultlocale()[0].split('_')[0]

	def __getitem__(self, lang: str) -> Language:
		"""Returns the Language object for the given language code.
		@param lang: two-character language code
		@type lang: str
		@return: the Language object for the given code
		@rtype: Language
		"""
		return Language(lang, self.names)


# Languages which may not be in the main list
langNames = {
	# Translators: The name of the language, which may not be in the main list
	"ceb": _("Cebuano"),
	# Translators: The name of the language, which may not be in the main list
	"eo": _("Esperanto"),
	# Translators: The name of the language, which may not be in the main list
	"hmn": _("Hmong"),
	# Translators: The name of the language, which may not be in the main list
	"ht": _("Creole Haiti"),
	# Translators: The name of the language, which may not be in the main list
	"jv": _("Javanese"),
	# Translators: The name of the language, which may not be in the main list
	"la": _("Latin"),
	# Translators: The name of the language, which may not be in the main list
	"mg": _("Malagasy"),
	# Translators: The name of the language, which may not be in the main list
	"mhr": _("Meadow Mari"),
	# Translators: The name of the language, which may not be in the main list
	"mrj": _("Hill Mari"),
	# Translators: The name of the language, which may not be in the main list
	"my": _("Myanmar (Burmese)"),
	# Translators: The name of the language, which may not be in the main list
	"ny": _("Chichewa"),
	# Translators: The name of the language, which may not be in the main list
	"so": _("Somali"),
	# Translators: The name of the language, which may not be in the main list
	"st": _("Sesotho"),
	# Translators: The name of the language, which may not be in the main list
	"su": _("Sundanese"),
	# Translators: The name of the language, which may not be in the main list
	"tl": _("Tagalog"),
	# Translators: The name of the language, which may not be in the main list
	"yi": _("Yiddish"),
}

# List of language pairs available in the dictionary
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

# An instance of the Languages object for use in the add-on
langs = Languages(availableLanguages, langNames)
