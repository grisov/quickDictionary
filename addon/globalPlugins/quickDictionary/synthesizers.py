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


class Profiles(object):

	def __init__(self):
		self._path = os.path.join(config.getUserDefaultConfigPath(), "%s.pickle" % _addonName)
		self._profs = {}
		self._default = Profile().update()
		self.load()

	def load(self):
		if not os.path.exists(self._path): return
		with open(self._path, 'rb') as f:
			data = pickle.load(f)
		if 'version' not in data:
			data = {'version': 0}
		self._profs = dict((key, Profile(val['name'], val['conf'], val['lang'])) if isinstance(key,int) else (key,val) for key,val in data.items())

	def save(self):
		profs = {}
		for slot in sorted(self._profs, key=lambda slot: str(slot)):
			if isinstance(slot, int):
				profs[slot] = {
					'name': self._profs[slot].name,
					'conf': self._profs[slot].conf,
					'lang': self._profs[slot].lang
				}
			else:
				profs[slot] = self._profs[slot]
		with open(self._path, 'wb') as f:
			pickle.dump(profs, f)

	def __getitem__(self, id):
		if id not in self._profs:
			self._profs[id] = Profile()
		return self._profs[id]

	def __iter__(self):
		for slot in sorted(self._profs, key=lambda s: str(s)):
			if isinstance(slot, int):
				yield slot, self._profs[slot]

	def remove(self, id: int):
		try:
			self._profs.pop(id)
		except KeyError:
			pass

	def currentAsDefault(self):
		self._default = Profile().update()

	def restoreDefault(self):
		self._default.set()
