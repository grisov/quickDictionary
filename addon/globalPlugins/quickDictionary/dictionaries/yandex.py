#yandex.py
# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.
# See the file COPYING for more details.
# Copyright (C) 2020 Olexandr Gryshchenko <grisov.nvaccess@mailnull.com>

import os
from importlib import import_module
from ..locator import service_provider, DictionaryService

PACKAGE = __name__.replace('.' + os.path.basename(os.path.dirname(__file__)), '')


@service_provider(DictionaryService)
class YandexDictionary(DictionaryService):
	"""Representation of the online dictionary service."""

	# Used to set the sort order of a list of services
	id: int = 1

	@property
	def name(self) -> str:
		"""Short service name.
		Matches the name of the file representing the service and - the name of the directory containing the service modules.
		@return: service name
		@rtype: str
		"""
		return import_module('.dictionary', package=PACKAGE).NAME

	@property
	def summary(self) -> str:
		"""Service summary - Appears in the services list and in the settings panel.
		@return service summary
		@rtype: str
		"""
		return import_module('.dictionary', package=PACKAGE).SUMMARY

	@property
	def confspec(self) -> dict:
		"""Service configuration scheme.
		@return: configuration scheme
		@rtype: dict
		"""
		return import_module('.dictionary', package=PACKAGE).confspec

	@property
	def translator(self) -> object:
		"""A link to the class used by the service to receive translations from the online dictionary.
		@return: object type used by the service
		@rtype: object, usually inherited from <service_name>.dictionary.Translator
		"""
		return import_module('.dictionary', package=PACKAGE).Translator

	@property
	def langs(self) -> object:
		"""An instance of the Languages class to interact with lists of languages available in the online service.
		@return: an instance of the class to interact with the list of available languages
		@rtyp: object, usually instance of <service_name>.languages.Languages
		"""
		return import_module('.languages', package=PACKAGE).langs

	@property
	def settings(self) -> object:
		"""A link to the class that represents the settings panel of the selected service.
		@return: link to the add-on settings panel
		@rtype: object, usually inherited from graphui.QDSettingsPanel
		"""
		return import_module('.settings', package=PACKAGE).QuickDictionarySettingsPanel
