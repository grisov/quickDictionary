#languages.py
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

import os
import json
import config
import ssl
from languageHandler import getLanguageDescription
from locale import getdefaultlocale
from urllib.request import Request, urlopen
from .secret import APIKEY as TOKEN
from . import _addonName

ssl._create_default_https_context = ssl._create_unverified_context


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
		if self.lang=='':
			name = "- %s -" % name
		if not name:
			name = self.names.get(self.lang, None)
		return name or self.lang


class Languages(object):
	"""Represents a list of languages available in the dictionary service."""

	def __init__(self, file: str, langNames:dict):
		"""Initialization of an object representing a list of available language pairs.
		@param file: external file containing a list of available source and target languages
		@type file: str
		@param langNames: additional languages, where key is a two-character code and value is name of the language
		@type langNames: dict
		"""
		self.file = file
		self.langs = self.load()
		self.names = langNames
		self.updated = False

	def load(self) -> list:
		"""Loads a list of available language pairs from an external json file.
		@return: list of language pairs available in the dictionary
		@rtype: list
		"""
		data = []
		with open(self.file, 'r', encoding='utf-8') as f:
			data = json.load(f)
		return data

	def update(self) -> bool:
		"""Get a list of available language pairs from a remote server and save them in an external file.
		@return: the success status of the operation
		@rtype: bool
		"""
		langs = []
		headers = {
			'User-Agent': 'Mozilla 5.0'}
		directUrl = 'https://dictionary.yandex.net'
		mirrorUrl = 'https://info.alwaysdata.net'
		servers = [mirrorUrl]
		if not config.conf[_addonName]['mirror']:
			servers.insert(0, directUrl)
		urlTemplate = "{server}/api/v1/dicservice.json/getLangs?key={key}"
		for server in servers:
			url = urlTemplate.format(server=server, key = TOKEN)
			rq = Request(url, method='GET', headers=headers)
			try:
				resp = urlopen(rq, timeout=8)
			except Exception as e:
				log.exception(e)
				continue
			if resp.status!=200:
				log.error("Incorrect response code %d from the server %s", resp.status, server)
				continue
			langs = json.loads(resp.read().decode())
			break
		if len(langs)>5:
			with open(self.file, 'w') as f:
				f.write(json.dumps(langs, skipkeys=True, ensure_ascii=False, indent=4))
			self.updated = True
		return self.updated

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


# An instance of the Languages object for use in the add-on
langs = Languages("%s.%s" % (os.path.splitext(os.path.abspath(__file__))[0], 'json'), langNames)
