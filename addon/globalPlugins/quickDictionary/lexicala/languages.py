#languages.py
# Description of the class for working with the languages of a specific service
# A part of the NVDA Quick Dictionary add-on
# This file is covered by the GNU General Public License.
# See the file COPYING for more details.
# Copyright (C) 2020-2021 Olexandr Gryshchenko <grisov.nvaccess@mailnull.com>

from typing import List, Dict, Iterator
import os
import config
from .. import _addonName
from ..service import Language, Languages, secrets
from .api import Lapi, serviceName


class ServiceLanguage(Language):
	"""Overriding a class due to a non-compliance of the some language codes with the ISO standard."""

	def __init__(self, code: str) -> None:
		"""Language initialization by its code."""
		super(ServiceLanguage, self).__init__(code)

	@property
	def name(self) -> str:
		"""Full language name.
		@return: language name
		@rtype: str
		"""
		code = {	# a detailed list of used languages can be found in the <languages.json> file
			'br': 'pt_br',	# Brazilian Portuguese
			'da': 'fr_ca',	# Canadian French
			'dk': 'da',	# Danish
			'tw': 'zh_tw',	# Traditional Chinese
			}.get(self.code, self.code)
		return super(ServiceLanguage, self).getName(code)


class ServiceLanguages(Languages):
	"""Represents a list of languages available in the dictionary service."""

	def __init__(self, file: str = "%s.json" % os.path.splitext(os.path.abspath(__file__))[0]):
		"""Initialization of an object representing a collection of available language pairs.
		Inherited methods from the parent class: load, save, __getitem__ and locale property
		Must be implemented: fromList, intoList, update, isAvailable and properties defaultFrom, defaultInto, all
		@param file: external file containing a list of available source and target languages
		@type file: str
		"""
		self.updated = False
		self._all: List[ServiceLanguage] = []
		self._langs: Dict = {}
		super(ServiceLanguages, self).__init__(file)

	@property
	def sources(self) -> List[str]:
		"""List of source dictionary names available in the online service.
		@return: list of source dictionaries
		@rtype: List[str]
		"""
		return list(self._langs.get('resources', []))

	@property
	def source(self) -> str:
		"""Return the name of the currently selected source dictionary.
		@return: name of the selected source dictionary
		@rtype: str
		"""
		return config.conf.get(_addonName, {}).get(serviceName, {}).get('source') or self.defaultSource

	@source.setter
	def source(self, source:str):
		"""Set the name of the source dictionary as selected for translations.
		@param source: name of the source dictionary
		@type source: str
		"""
		if source in self.sources:
			config.conf[_addonName][serviceName]['source'] = source

	@property
	def defaultSource(self) -> str:
		"""Return the default source dictionary name required for service initialization.
		@return: name of source dictionary
		@rtype: str
		"""
		favorite = 'password'
		return favorite if favorite in self.sources else next(iter(self.sources), 'global')

	def update(self) -> bool:
		"""Get a list of available language pairs from a remote server and save them in an external file.
		This method should save the result of the operation in the logical field <self.updated>.
		@return: the success status of the operation
		@rtype: bool
		"""
		self.updated = False
		langs = Lapi().languages()
		if len(langs.get('resources', []))>=3:
			self.updated = self.save(langs)
		return self.updated

	def fromList(self, source: str='') -> Iterator[ServiceLanguage]:
		"""Sequence of available source languages.
		@param source: source dictionary name, if not specified, the current is used
		@type source: str
		@return: sequence of available source languages
		@rtype: Iterator[ServiceLanguage]
		"""
		source = source or self.source
		for lang in self._langs.get('resources', {}).get(source, {}).get('source_languages', []):
			yield ServiceLanguage(lang)

	def intoList(self, source: str='') -> Iterator[ServiceLanguage]:
		"""Sequence of available target languages.
		@param source: source dictionary name, if not specified, the current is used
		@type source: str
		@return: sequence of available target languages
		@rtype: Iterator[ServiceLanguage]
		"""
		source = source or self.source
		for lang in self._langs.get('resources', {}).get(source, {}).get('target_languages', []):
			yield ServiceLanguage(lang)

	def isAvailable(self, source: str, target: str) -> bool:
		"""Indicates whether the selected language pair is in the list of available languages.
		@param source: source language code
		@type source: str
		@param target: target language code
		@type target: str
		@return: whether a language pair is present in the list of available
		@rtype: bool
		"""
		return (source in [lang.code for lang in self.fromList()]) and (target in [lang.code for lang in self.intoList()])

	@property
	def defaultFrom(self) -> ServiceLanguage:
		"""Default source language.
		@return: English if available, else - the first language in list of source languages
		@rtype: ServiceLanguage
		"""
		return ServiceLanguage('en' if 'en' in self._langs['resources'][self.defaultSource]['source_languages'] else next(iter(self._langs['resources'][self.defaultSource]['source_languages']), ''))

	@property
	def defaultInto(self) -> ServiceLanguage:
		"""Default target language.
		@return: locale language, if it is available as the target for the default source, otherwise the first one in the list
		@rtype: ServiceLanguage
		"""
		return ServiceLanguage(self.locale.code if self.locale.code in self._langs['resources'][self.defaultSource]['target_languages'] else next(iter(self._langs['resources'][self.defaultSource]['target_languages']), ''))

	@property
	def all(self) -> List:
		"""Full list of all supported source and target languages.
		@return: list of all supported languages
		@rtype: List[ServiceLanguage]
		"""
		if not self._all:
			_all: List[str] = []
			for source in self.sources:
				_all.extend(self._langs.get('resources', {}).get(source, {}).get('source_languages', []))
				_all.extend(self._langs.get('resources', {}).get(source, {}).get('target_languages', []))
			self._all = [ServiceLanguage(lang) for lang in frozenset(_all)]
		return self._all


# An instance of the Languages object for use in the add-on
langs = ServiceLanguages()
