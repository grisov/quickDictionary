#yandex.py
import os
from importlib import import_module
from ..locator import service_provider, DictionaryService

PACKAGE = __name__.replace('.' + os.path.basename(os.path.dirname(__file__)), '')


@service_provider(DictionaryService)
class YandexDictionary(DictionaryService):

	@property
	def name(self):
		return import_module('.dictionary', package=PACKAGE).NAME

	@property
	def summary(self):
		return import_module('.dictionary', package=PACKAGE).SUMMARY

	@property
	def confspec(self):
		return import_module('.dictionary', package=PACKAGE).confspec

	@property
	def translator(self):
		return import_module('.dictionary', package=PACKAGE).Translator

	@property
	def langs(self):
		return import_module('.languages', package=PACKAGE).langs

	@property
	def settings(self):
		return import_module('.settings', package=PACKAGE).QuickDictionarySettingsPanel
