#service.py
"""
	Description of common components for:
	* working with languages (class Languages);
	* executing translation requests (class Translator);
	* credentials management for all connected services (class Secrets).
	Relevant service classes must be inherited from Languages and Translator objects

	A part of the NVDA Quick Dictionary add-on
	This file is covered by the GNU General Public License.
	See the file COPYING for more details.
	Copyright (C) 2020-2021 Olexandr Gryshchenko <grisov.nvaccess@mailnull.com>
"""

from __future__ import annotations
from typing import Callable, Union, List, Dict, Generator
import addonHandler
from logHandler import log
try:
	addonHandler.initTranslation()
except addonHandler.AddonError:
	log.warning("Unable to initialise translations. This may be because the addon is running from NVDA scratchpad.")
_: Callable[[str], str]

import os.path
import json
import zlib
import binascii
import zipfile
from abc import ABCMeta, abstractmethod
from threading import Thread
from locale import getdefaultlocale
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

	def __init__(self,
		code: str,
		langNames: Dict[str, str] = langNames) -> None:
		"""Language object fields initialization.
		@param code: usually two-character language code
		@type code: str
		@param langNames: additional languages, where key is a two-character code and value is name of the language
		@type langNames: Dict[str, str]
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
		@return: language name
		@rtype: str
		"""
		return self.getName()

	def getName(self, code: str='') -> str:
		"""Full language name.
		If it is not possible to determine, a short language code is returned.
		It is designed as a separate method for redefining it in child classes of services
		because some services use language codes that do not comply with the ISO standard.
		@param code: language code if not specified, the value of the internal field of the class is taken
		@type code: str
		@return: language name
		@rtype: str
		"""
		lang = code or self._lang
		name = getLanguageDescription(lang)
		if self._lang=='':
			name = "- %s -" % name
		if not name:
			name = self._names.get(lang)
		return name or lang


class Languages(metaclass=ABCMeta):
	"""Represents a list of languages available in the dictionary service."""

	def __init__(self, file: str) -> None:
		"""Initialization of an object representing a list of available language pairs.
		@param file: external file containing a list of available source and target languages
		@type file: str
		"""
		self._file = file
		self._langs: Union[List, Dict] = self.load()

	def load(self) -> Union[List, Dict]:
		"""Load a collection of available language pairs from an external json file.
		@return: collection of language pairs available in the dictionary
		@rtype: Union[List, Dict] (depends on the service)
		"""
		data = {}
		try:
			with open(self._file, 'r', encoding='utf-8') as f:
				data = json.load(f)
		except Exception as e:
			log.exception(e)
		return data.get('data', {})

	def save(self, data: Union[List, Dict]) -> bool:
		"""Save a collection of available languages to an external file.
		@param data: collection of available languages
		@type data: Union[List, Dict]
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
		try:
			code: str = getattr(getdefaultlocale()[0], 'split')('_')[0]
		except (AttributeError, IndexError,):
			code = ''
		return Language(code)

	def __contains__(self, lang: Language) -> bool:
		"""Implementation of checking the presence of an Language in the current collection.
		@param lang: language is represented as a Language object
		@type lang: Language
		@return: whether the specified language is available in the current list
		@rtype: bool
		"""
		for language in self.all:
			if language.code==lang.code:
				return True
		return False

	def __getitem__(self, lang: str) -> Language:
		"""Returns the Language object for the given language code.
		@param lang: two-character language code
		@type lang: str
		@return: the Language object for the given code
		@rtype: Language
		"""
		return Language(lang)

	# The following methods and properties must be overridden in the child class
	@abstractmethod
	def update(self) -> bool:
		"""Get a list of available language pairs from a remote server and save them in an external file.
		Also, this method should save the result of the operation in the logical field <self.updated>.
		@return: the success status of the operation
		@rtype: bool
		"""
		raise NotImplementedError("This method must be overridden in the child class!")

	@abstractmethod
	def fromList(self) -> Generator[Language, None, None]:
		"""Sequence of available source languages.
		@return: sequence of available source languages
		@rtype: Generator[Language, None, None]
		"""
		raise NotImplementedError("This method must be overridden in the child class!")

	@abstractmethod
	def intoList(self, lang: str) -> Generator[Language, None, None]:
		"""Sequence of available target languages for a given source language.
		@param lang: source language code
		@type lang: str
		@return: sequence of available target languages
		@rtype: Generator[Language, None, None]
		"""
		raise NotImplementedError("This method must be overridden in the child class!")

	@abstractmethod
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
	@abstractmethod
	def defaultFrom(self) -> Language:
		"""Default source language.
		@return: 'en' if available, else - the first language in list of source languages
		@rtype: Language
		"""
		raise NotImplementedError("This property must be overridden in the child class!")

	@property
	@abstractmethod
	def defaultInto(self) -> Language:
		"""Default target language.
		@return: locale language, if it is available as the target for the default source, otherwise the first one in the list
		@rtype: Language
		"""
		raise NotImplementedError("This property must be overridden in the child class!")

	@property
	@abstractmethod
	def all(self) -> List[Language]:
		"""Full list of all supported source and target languages.
		@return: list of all supported languages
		@rtype: List[Language]
		"""
		raise NotImplementedError("This property must be overridden in the child class!")


class Translator(Thread):
	"""Provides interaction with the online dictionary service."""

	def __init__(self,
		langFrom: str,
		langTo: str,
		text: str,
		*args, **kwargs) -> None:
		"""Initialization of the source and target language, as well as the word or phrase to search in the dictionary.
		@param langFrom: source language
		@type langFrom: str
		@param langTo: target language
		@type langTo: str
		@param text: a word or phrase to look up in a dictionary
		@type text: str
		"""
		super(Translator, self).__init__(*args, **kwargs)
		self._langFrom = langFrom
		self._langTo = langTo
		self._text = text
		self._html = ''
		self._plaintext = ''
		self._error = False

	@property
	def langFrom(self) -> str:
		"""Source language code.
		@return: language code
		@rtype: str
		"""
		return self._langFrom

	@property
	def langTo(self) -> str:
		"""Target language code.
		@return: language code
		@rtype: str
		"""
		return self._langTo

	@property
	def text(self) -> str:
		"""Text to send to a remote dictionary service.
		@return: word or phrase
		@rtype: str
		"""
		return self._text

	@property
	def html(self) -> str:
		"""Response from the remote service in the HTML format.
		@return: hypertext string
		@rtype: str
		"""
		return self._html

	@property
	def plaintext(self) -> str:
		"""Response from the remote service in the plain text format.
		@return: plain text string
		@rtype: str
		"""
		return self._plaintext

	@property
	def error(self) -> bool:
		"""Were there any errors in the remote service request?
		@return: a sign of errors
		@rtype: bool
		"""
		return self._error

	def __hash__(self) -> int:
		"""Make the class hashable with a constant hash value.
		This is necessary for the caching performed by the decorator functools.lru_cache to work correctly.
		@return: numeric value of the hash
		@rtype: int, always 0
		"""
		return 0

	def run(self) -> None:
		"""Query the remote dictionary and save the processed response.
		Should run in a separate thread to avoid blocking.
		"""
		raise NotImplementedError("This method must be overridden in the child class!")


class Secret(object):
	"""An object that stores credentials for the selected service."""

	def __init__(self, service: str) -> None:
		"""Initialization of required fields.
		@param service: online dictionary service name, determined by the module "locator"
		@type service: str
		"""
		self._service: str = service
		self._url: str = ''
		self.username: str = ''
		self.password: str = ''

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
	def username(self, name: str) -> None:
		"""Set the username for the specified service.
		@param name: name of user if necessary
		@type name: str
		"""
		self._username = self.encode(name)

	@property
	def password(self) -> str:
		"""The password required to log in to the selected online service.
		@return: user password, empty string by default
		@rtype: str
		"""
		return self.decode(self._password)

	@password.setter
	def password(self, pwd: str) -> None:
		"""Set the password required to log in to the selected online service.
		@param pwd: user password if necessary
		@type pwd: str
		"""
		self._password = self.encode(pwd)

	@property
	def url(self) -> str:
		"""The address of the registration web page in the selected service.
		@return: Registration URL for the selected service
		@rtype: str
		"""
		return self._url

	@url.setter
	def url(self, link: str) -> None:
		"""Set the url of the web page to register in the specified web service.
		@param link: the URL of the registration web page
		@type link: str
		"""
		self._url = link

	def encode(self, cred: str) -> str:
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

	def decode(self, cred: str) -> str:
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

	def toDict(self) -> Dict[str, str]:
		"""Convert a set of values stored in an object to a dict type.
		@return: dict, which contains the values of all fields of the current object
		@rtype: Dict[str, str]
		"""
		return {
			"service": self._service,
			"username": self._username,
			"password": self._password,
			"url": self._url
		}

	def fromDict(self, rec: Dict[str, str]) -> Secret:
		"""Initialize the fields of the current object from the obtained parameter.
		The update occurs only when the name of the service in the corresponding field coincides with the current one.
		@param rec: dict object with required keys
		@type rec: Dict[str, str]
		@return: updated object with the obtained data
		@rtype: Secret
		"""
		if self._service == rec.get('service'):
			self._username = rec.get('username') or self._username
			self._password = rec.get('password') or self._password
			self._url = rec.get('url') or self._url
		return self


class Secrets(object):
	"""Manage the credentials required for all add-on services to work."""

	def __init__(self,
		dir: str = os.path.dirname(__file__),
		file: str = 'qd') -> None:
		"""Initialize all required values.
		@param dir: the directory where the credential file is stored
		@type dir: str
		@param file: file name without extension, as this json file will be stored in the zip archive of the same name
		@type file: str
		"""
		self._path: str = os.path.join(dir, file)
		self._file: str = file + '.json'
		self._secrets: Dict[str, Secret] = {}
		self.load()

	def load(self) -> Secrets:
		"""Load credentials from an archived file.
		@return: updated object with loaded credentials
		@rtype: Secrets
		"""
		data: Dict[str, Dict[str, str]] = {}
		try:
			with zipfile.ZipFile(self._path+'.zip', mode='r') as zipArchive:
				with zipArchive.open(name=self._file, mode='r', pwd=_addonName.encode('utf-8')) as unzippedFile:
					data = json.load(unzippedFile)
		except Exception as e:
			log.error("%s: %s, %s", str(e), self._path+'.zip', self._file)
		for service in data:
			self._secrets[service] = Secret(service).fromDict(data.get(service, {}))
		return self

	def save(self) -> Secrets:
		"""Save the current credentials of all services to an json file.
		@return: current updated object
		@rtype: Secrets
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
	def services(self) -> List[str]:
		"""List of names of all services for which credentials are available.
		@return: list of service names, determined by the module "locator"
		@rtype: List[str]
		"""
		return list(self._secrets)

	def __getitem__(self, service: str) -> Secret:
		"""Return the saved credentials for the service by its name.
		@param service: service name, determined by the module "locator"
		@type service: str
		@return: credentials required for authorization in the selected service
		@rtype: Secret
		"""
		return self._secrets.get(service, Secret(service))


# an instance for further use in addon services is created here so as not to perform its initialization on each call
secrets = Secrets()
