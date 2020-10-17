#yandex.py
import os
from importlib import import_module
from ..locator import service_provider
from ..service import DictionaryService

PACKAGE = __name__.replace('.' + os.path.basename(os.path.dirname(__file__)), '')


@service_provider(DictionaryService)
class YandexDictionary(DictionaryService):

	@property
	def label(self):
		return os.path.splitext(os.path.basename(__file__))[0]

	def translator(self):
		return import_module('.dictionary', package=PACKAGE).Translator

	def langs(self):
		return import_module('.languages', package=PACKAGE).langs

	def settings(self):
		return import_module('.settings', package=PACKAGE).QuickDictionarySettingsPanel

	def secret(self):
		return import_module('.secret', package=PACKAGE)
