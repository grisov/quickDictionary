#languages.py
# Description of common components for working with languages
# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.
# See the file COPYING for more details.
# Copyright (C) 2020 Olexandr Gryshchenko <grisov.nvaccess@mailnull.com>

import addonHandler
from logHandler import log
try:
	addonHandler.initTranslation()
except addonHandler.AddonError:
	log.warning("Unable to initialise translations. This may be because the addon is running from NVDA scratchpad.")

import json
from languageHandler import getLanguageDescription
from locale import getdefaultlocale


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

class Language(object):
	"""Object representation of language."""

	def __init__(self, code:str, langNames:dict = langNames):
		"""Language object fields initialization.
		@param code: usually two-character language code
		@type code: str
		@param langNames: additional languages, where key is a two-character code and value is name of the language
		@type langNames: dict
		"""
		self._lang = code
		self._names = langNames

	@property
	def code(self) -> str:
		"""Language code.
		@return: usually two-character language code
		@rtype: str
		"""
		return self._lang

	@property
	def name(self) -> str:
		"""Full language name.
		If it is not possible to determine, a short language code is returned.
		@return: language name
		@rtype: str
		"""
		name = getLanguageDescription(self._lang)
		if self._lang=='':
			name = "- %s -" % name
		if not name:
			name = self._names.get(self._lang, None)
		return name or self._lang


class ServiceLanguages(object):
	"""Represents a list of languages available in the dictionary service."""

	def __init__(self, file: str):
		"""Initialization of an object representing a list of available language pairs.
		@param file: external file containing a list of available source and target languages
		@type file: str
		"""
		self._file = file
		self._langs = self.load()

	def load(self):
		"""Load a collection of available language pairs from an external json file.
		@return: collection of language pairs available in the dictionary
		@rtype: list or dict (depends on the service)
		"""
		data = {}
		try:
			with open(self._file, 'r', encoding='utf-8') as f:
				data = json.load(f)
		except Exception as e:
			log.exception(e)
		return data.get('data')

	def save(self, data) -> bool:
		"""Save a collection of available languages to an external file.
		@param data: collection of available languages
		@type data: list or dict
		"""
		try:
			with open(self._file, 'w') as f:
				f.write(json.dumps({"data": data}, skipkeys=True, ensure_ascii=False, indent=4))
		except Exception as e:
			log.exception(e)
			return False
		return True

	@property
	def locale(self) -> Language:
		"""User locale language.
		@return: locale language used on the user's computer
		@rtype: Language
		"""
		code = getdefaultlocale()[0].split('_')[0]
		return Language(code)

	def __getitem__(self, lang: str) -> Language:
		"""Returns the Language object for the given language code.
		@param lang: two-character language code
		@type lang: str
		@return: the Language object for the given code
		@rtype: Language
		"""
		return Language(lang)

	# The following methods and properties must be overridden in the child class
	def update(self) -> bool:
		"""Get a list of available language pairs from a remote server and save them in an external file.
		Also, this method should save the result of the operation in the logical field <self.updated>.
		@return: the success status of the operation
		@rtype: bool
		"""
		raise NotImplementedError("This method must be overridden in the child class!")

	def fromList(self) -> list:
		"""Sequence of available source languages.
		@return: sequence of available source languages
		@rtype: list of Language objects
		"""
		raise NotImplementedError("This method must be overridden in the child class!")

	def intoList(self, lang: str) -> list:
		"""Sequence of available target languages for a given source language.
		@param lang: source language code
		@type lang: str
		@return: sequence of available target languages
		@rtype: list of Language objects
		"""
		raise NotImplementedError("This method must be overridden in the child class!")

	def isAvailable(self, source: str, target: str) -> bool:
		"""Indicates whether the selected language pair is in the list of available languages.
		@param source: source language code
		@type source: str
		@param target: target language code
		@type target: str
		@return: whether a language pair is present in the list of available
		@rtype: bool
		"""
		raise NotImplementedError("This method must be overridden in the child class!")

	@property
	def defaultFrom(self) -> str:
		"""Default source language.
		@return: 'en' if available, else - the first language in list of source languages
		@rtype: str
		"""
		raise NotImplementedError("This property must be overridden in the child class!")

	@property
	def defaultInto(self) -> str:
		"""Default target language.
		@return: locale language, if it is available as the target for the default source, otherwise the first one in the list
		@rtype: str
		"""
		raise NotImplementedError("This property must be overridden in the child class!")

	@property
	def all(self) -> list:
		"""Full list of all supported source and target languages.
		@return: list of all supported languages
		@rtype: list of Language
		"""
		raise NotImplementedError("This property must be overridden in the child class!")
