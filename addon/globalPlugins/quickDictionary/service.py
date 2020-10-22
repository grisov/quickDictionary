#service.py
"""
	Description of common components for:
	* working with languages (class Languages);
	* executing translation requests (class Translator);
	* credentials management for all connected services (class Secrets).
	Relevant service classes must be inherited from Languages and Translator objects

	A part of NonVisual Desktop Access (NVDA)
	This file is covered by the GNU General Public License.
	See the file COPYING for more details.
	Copyright (C) 2020 Olexandr Gryshchenko <grisov.nvaccess@mailnull.com>
"""
import addonHandler
from logHandler import log
try:
	addonHandler.initTranslation()
except addonHandler.AddonError:
	log.warning("Unable to initialise translations. This may be because the addon is running from NVDA scratchpad.")

import os
import json
import zlib
import binascii
import zipfile
from locale import getdefaultlocale
from threading import Thread, Event
from languageHandler import getLanguageDescription
from . import _addonName


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


class Languages(object):
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


class Translator(Thread):
	"""Provides interaction with the online dictionary service."""

	def __init__(self, langFrom:str, langTo:str, text:str, *args, **kwargs):
		"""Initialization of the source and target language, as well as the word or phrase to search in the dictionary.
		@param langFrom: source language
		@type langFrom: str
		@param langTo: target language
		@type langTo: str
		@param text: a word or phrase to look up in a dictionary
		@type text: str
		"""
		super(Translator, self).__init__(*args, **kwargs)
		self._stopEvent = Event()
		self._langFrom = langFrom
		self._langTo = langTo
		self._text = text
		self._html = ''
		self._plaintext = ''

	# The list of getters defining parameters for working with the dictionary
	langFrom = lambda self: self._langFrom
	langTo = lambda self: self._langTo
	text = lambda self: self._text
	html = lambda self: self._html
	plaintext = lambda self: self._plaintext

	# Define class properties
	langFrom = property(langFrom)
	langTo = property(langTo)
	text = property(text)
	html = property(html)
	plaintext = property(plaintext)

	def _stop(self, *args, **kwargs):
		"""Executed when a process terminates in a thread."""
		super(Translator, self)._stop(*args, **kwargs)
		self._stopEvent.set()

	def __hash__(self) -> int:
		"""Make the class hashable with a constant hash value.
		This is necessary for the caching performed by the decorator functools.lru_cache to work correctly.
		@return: numeric value of the hash
		@rtype: int, always 0
		"""
		return 0

	def run(self):
		"""Query the remote dictionary and save the processed response.
		Should run in a separate thread to avoid blocking.
		"""
		raise NotImplementedError("This method must be overridden in the child class!")


class Secret(object):
	"""An object that stores credentials for the selected service."""

	def __init__(self, service:str):
		"""Initialization of required fields.
		@param service: online dictionary service name, determined by the module "locator"
		@type service: str
		"""
		self._service = service
		self._url = ''
		self.username = ''
		self.password = ''

	@property
	def service(self) -> str:
		"""The name of the service to which the object is bound.
		@return: online dictionary service name
		@rtype: str
		"""
		return self._service

	@property
	def username(self) -> str:
		"""The username used to log in to the service.
		@return: name of user, empty string by default
		@rtype: str
		"""
		return self.decode(self._username)

	@username.setter
	def username(self, name:str):
		"""Set the username for the specified service.
		@param name: name of user if necessary
		@type name: str
		@return: updated object with current username
		@rtype: service.Secret
		"""
		self._username = self.encode(name)
		return self

	@property
	def password(self) -> str:
		"""The password required to log in to the selected online service.
		@return: user password, empty string by default
		@rtype: str
		"""
		return self.decode(self._password)

	@password.setter
	def password(self, pwd:str):
		"""Set the password required to log in to the selected online service.
		@param pwd: user password if necessary
		@type pwd: str
		@return: updated object with current password
		@rtype: service.Secret
		"""
		self._password = self.encode(pwd)
		return self

	@property
	def url(self) -> str:
		"""The address of the registration web page in the selected service.
		@return: Registration URL for the selected service
		@rtype: str
		"""
		return self._url

	@url.setter
	def url(self, link:str):
		"""Set the url of the web page to register in the specified web service.
		@param link: the URL of the registration web page
		@type link: str
		@return: updated object with current url-address
		@rtype: service.Secret
		"""
		self._url = link
		return self

	def encode(self, cred:str) -> str:
		"""Masking of input sensitive data for their further storage in the system.
		@param cred: credentials or other sensitive data
		@type cred: str
		@return: a string of hidden (masked) data
		@rtype: str
		"""
		try:
			return binascii.hexlify(zlib.compress(cred.encode('utf-8'), level=9)).decode()
		except Exception as e:
			return ''

	def decode(self, cred:str) -> str:
		"""Restore the original data from the previously masked string.
		@param cred: pre-hidden (masked) credentials or other sensitive data
		@type cred: str
		@return: restored data string in its original form
		@rtype: str
		"""
		try:
			return zlib.decompress(binascii.unhexlify(cred.encode('utf-8'))).decode()
		except Exception as e:
			return ''

	def toDict(self) -> dict:
		"""Convert a set of values stored in an object to a dict type.
		@return: dict, which contains the values of all fields of the current object
		@rtype: dict
		"""
		return {
			"service": self._service,
			"username": self._username,
			"password": self._password,
			"url": self._url
		}

	def fromDict(self, rec:dict):
		"""Initialize the fields of the current object from the obtained parameter.
		The update occurs only when the name of the service in the corresponding field coincides with the current one.
		@param rec: dict object with required keys
		@type rec: dict
		@return: updated object with the obtained data
		@rtype: service.Secret
		"""
		if self._service == rec.get('service'):
			self._username = rec.get('username') or self._username
			self._password = rec.get('password') or self._password
			self._url = rec.get('url') or self._url
		return self


class Secrets(object):
	"""Manage the credentials required for all add-on services to work."""

	def __init__(self, dir:str = os.path.dirname(__file__), file:str = 'credentials'):
		"""Initialize all required values.
		@param dir: the directory where the credential file is stored
		@type dir: str
		@param file: file name without extension, as this json file will be stored in the zip archive of the same name
		@type file: str
		"""
		self._path = os.path.join(dir, file)
		self._file = file + '.json'
		self._secrets = {}
		self.load()

	def load(self):
		"""Load credentials from an archived file.
		@return: updated object with loaded credentials
		@rtype: service.Secrets
		"""
		data = {}
		try:
			with zipfile.ZipFile(self._path+'.zip', mode='r') as zipArchive:
				with zipArchive.open(name=self._file, mode='r', pwd=_addonName.encode('utf-8')) as unzippedFile:
					data = json.load(unzippedFile)
		except Exception as e:
			log.error("%s: %s, %s", str(e), self._path+'.zip', self._file)
		for service in data:
			self._secrets[service] = Secret(service).fromDict(data.get(service))
		return self

	def save(self):
		"""Save the current credentials of all services to an json file.
		@return: current object
		@rtype: service.Secrets
		"""
		data = {}
		for service in self._secrets:
			data[service] = self._secrets[service].toDict()
		try:
			with open(self._path+'.json', 'w', encoding='utf-8') as f:
				f.write(json.dumps(data, skipkeys=True, ensure_ascii=False, indent=4))
		except Exception as e:
			log.error(str(e), self._path+'json')
		return self

	@property
	def services(self) -> list:
		"""List of names of all services for which credentials are available.
		@return: list of service names, determined by the module "locator"
		@rtype: list of str
		"""
		return list(self._secrets)

	def __getitem__(self, service:str) -> Secret:
		"""Return the saved credentials for the service by its name.
		@param service: service name, determined by the module "locator"
		@type service: str
		@return: credentials required for authorization in the selected service
		@rtype: service.Secret
		"""
		return self._secrets.get(service, Secret(service))


# an instance for further use in addon services is created here so as not to perform its initialization on each call
secrets = Secrets()
