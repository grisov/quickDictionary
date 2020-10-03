import os
import pickle
import speech
import config
from . import _addonName


class Profile(object):

	def __init__(self, synthName: str='', synthConf: dict={}, lang: str=''):
		self._name = synthName
		self._conf = synthConf
		self._lang = lang

	def set(self):
		try:
			config.conf.profiles[0]['speech'][self._name].clear()
			config.conf.profiles[0]['speech'][self._name].update(self._conf)
			config.conf['speech'][self._name]._cache.clear()
			speech.setSynth(self._name)
			speech.getSynth().saveSettings()
		except KeyError:
			pass
		return self

	def update(self):
		self._name = speech.getSynth().name
		self._conf = dict(config.conf['speech'][speech.getSynth().name].items())
		self._lang = self._lang or ''
		return self

	@property
	def name(self) -> str:
		return self._name

	@property
	def conf(self) -> dict:
		return self._conf

	@property
	def title(self) -> str:
		return '-'.join((self.name, self.conf.get('voice', ''),))

	@property
	def lang(self) -> str:
		return self._lang

	@lang.setter
	def lang(self, lang: str):
		self._lang = lang
		return self
