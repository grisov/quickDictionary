#synthesizers.py
# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.
# See the file COPYING for more details.
# Copyright (C) 2020 Olexandr Gryshchenko <grisov.nvaccess@mailnull.com>
# In the development of this module were used ideas from the Switch Synth add-on (thanks to Tyler Spivey)

import os
import pickle
import speech
import config
from . import _addonName

class Profile(object):
	"""Represents the profile of the voice synthesizer."""

	def __init__(self, synthName: str='', synthConf: dict={}, lang: str=''):
		"""Input data needed to initialize the synthesizer profile.
		@param synthName: short name of the voice synthesizer
		@type synthName: str
		@param synthConf: voice synthesizer settings
		@type synthConf: dict
		@param lang: the language code to which this profile is associated
		@type lang: str
		"""
		self._name = synthName
		self._conf = synthConf
		self._lang = lang

	def set(self) -> bool:
		"""Sets the profile as the current voice synthesizer.
		@return: an indication of whether the synthesizer has been successfully switched on
		@rtype: bool
		"""
		state = False
		try:
			config.conf.profiles[0]['speech'][self._name].clear()
			config.conf.profiles[0]['speech'][self._name].update(self._conf)
			config.conf['speech'][self._name]._cache.clear()
			state = speech.setSynth(self._name)
			speech.getSynth().saveSettings()
		except KeyError:
			pass
		return state

	def update(self):
		"""Stores all data of the current voice synthesizer in the profile.
		@return: updated voice synthesizer profile
		@rtype: synthesizers.Profile
		"""
		self._name = speech.getSynth().name
		self._conf = dict(config.conf['speech'][speech.getSynth().name].items())
		self._lang = self._lang or ''
		return self

	@property
	def name(self) -> str:
		"""Returns the name of the voice synthesizer stored in the profile.
		@return: name of the voice synthesizer
		@rtype: str
		"""
		return self._name

	@property
	def conf(self) -> dict:
		"""Returns a dict with voice synthesizer settings stored in the profile.
		@return: voice synthesizer settings
		@rtype: dict
		"""
		return self._conf

	@property
	def title(self) -> str:
		"""Returns the title of a profile consisting of the synthesizer name and some other specific information.
		@return: synthesizer name and voice name
		@rtype: str
		"""
		return '-'.join((self.name, self.conf.get('voice', ''),))

	@property
	def lang(self) -> str:
		"""Returns the language code to which the synthesizer profile is associated.
		@return: language code
		@rtype: str
		"""
		return self._lang

	@lang.setter
	def lang(self, lang: str):
		"""Sets the language code with which the synthesizer profile is associated.
		@param lang: language code
		@type lang: str
		@return: updated profile object
		@rtype: synthesizers.Profile
		"""
		self._lang = lang
		return self


class Profiles(object):
	"""Represents a collection of synthesizer profiles and methods for manipulating them."""

	def __init__(self):
		"""Incoming data to initialize the object."""
		# an external file that stores profile settings
		self._path = os.path.join(config.getUserDefaultConfigPath(), "%s.pickle" % _addonName)
		# a dict of slots and profiles that match them
		self._profs = {}
		# default synthesizer profile settings
		self._default = Profile().update()
		self.load()

	def load(self):
		"""Loads saved profiles from an external file.
		@return: updated Profiles object or None
		@rtype: synthesizers.Profiles or None
		"""
		if not os.path.exists(self._path): return
		with open(self._path, 'rb') as f:
			data = pickle.load(f)
		if 'version' not in data:
			data = {'version': 0}
		self._profs = dict((key, Profile(val['name'], val['conf'], val['lang'])) if isinstance(key,int) else (key,val) for key,val in data.items())
		return self

	def save(self):
		"""Saves synthesizers profile set data to an external file.
		@return: the current set of customized voice synthesizers profiles
		@rtype: synthesizers.Profiles
		"""
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
		return self

	def __getitem__(self, id: int):
		"""Returns a synthesizer profile object by its slot ID.
		@param id: profile ID, which is its slot on the user's keyboard from 1 to 9
		@type id: int [1-9]
		@return: previously saved profile or default profile
		@rtype: synthesizers.Profile
		"""
		if id not in self._profs:
			self._profs[id] = Profile()
		return self._profs[id]

	def __iter__(self):
		"""Iterate through all available profiles of synthesizers.
		@return: iterator each element of which consists of two values - the slot number and the corresponding profile
		@rtype: (int, synthesizers.Profile) iterator
		"""
		for slot in sorted(self._profs, key=lambda s: str(s)):
			if isinstance(slot, int):
				yield slot, self._profs[slot]

	def __len__(self):
		"""Returns the number of voice synthesizers profiles available in the collection.
		@return: the number of profiles saved in the collection
		@rtype: int
		"""
		return(len(self._profs))

	def remove(self, id: int):
		"""Deletes the synthesizer profile by its specified ID (slot).
		@param id: profile ID (the slot with which it is associated)
		@type id: int
		@return: deleted profile from collection or None if such ID is not present in collection
		@rtype: synthesizers.Profile or None
		"""
		try:
			prof = self._profs.pop(id)
		except KeyError:
			prof = None
		return prof

	def currentAsDefault(self):
		"""Save the current voice as the default synthesizer.
		@return: current synthesizer profile
		@rtype: synthesizers.Profile
		"""
		self._default = Profile().update()
		return self._default

	def restoreDefault(self):
		"""Restores the default synthesizer that was saved earlier.
		@return: the default synthesizer profile that was saved earlier
		@rtype: synthesizers.Profile
		"""
		self._default.set()
		return self._default


# An instance of the Profiles object for later use in the add-on
profiles = Profiles()
