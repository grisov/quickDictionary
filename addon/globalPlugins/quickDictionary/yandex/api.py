# api.py
# Provides interaction with the Yandex online dictionary API
# A part of the NVDA Quick Dictionary add-on
# This file is covered by the GNU General Public License.
# See the file COPYING for more details.
# Copyright (C) 2020-2025 Olexandr Gryshchenko <grisov.nvaccess@mailnull.com>

from typing import Any, Dict
import os.path
import ssl
from urllib.request import Request, urlopen
from urllib.parse import quote as urlencode
from json import loads
import config
from .. import addonName
from ..service import secrets

ssl._create_default_https_context = ssl._create_unverified_context
serviceName: str = os.path.basename(os.path.dirname(__file__))
stat: Dict[str, Any] = {}  # Object for store statistics


class Yapi(object):
	"""Description of the Yandex Online Dictionary API."""

	def __init__(
		self,
		text: str = '',
		langFrom: str = '',
		langTo: str = '',
		uiLang: str = ''
	) -> None:
		"""Input parameters for interacting with the online dictionary.
		@param text: word or phrase to search in the dictionary
		@type text: str
		@param langFrom: source search language
		@type langFrom: str
		@param langTo: target search language
		@type langTo: str
		@param uiLang: language of user interface messages
		@type uiLang: str
		"""
		self._directUrl: str = "https://dictionary.yandex.net"
		self._mirrorUrl: str = "https://info.alwaysdata.net"
		self._text = text
		self._langFrom = langFrom
		self._langTo = langTo
		self._uiLang = uiLang
		self._headers: Dict[str, str] = {
			'User-Agent': 'Mozilla 5.0'}

	@property
	def text(self) -> str:
		"""Word or phrase to search in the dictionary.
		@return: the value of the text field
		@rtype: str
		"""
		return self._text

	@property
	def langFrom(self) -> str:
		"""Source search language.
		@return: the value of the source language field
		@rtype: str
		"""
		return self._langFrom

	@property
	def langTo(self) -> str:
		"""Target search language.
		@return: the value of the target language field
		@rtype: str
		"""
		return self._langTo

	@property
	def uiLang(self) -> str:
		"""Language of user interface messages.
		@return: the value of the user interface language field
		@rtype: str
		"""
		return self._uiLang

	@property
	def mirror(self) -> bool:
		"""Indicate whether to use an alternate server first.
		@return: the order of the servers used when connecting
		@rtype: bool
		"""
		return config.conf[addonName][serviceName]['mirror']

	@property
	def directUrl(self) -> str:
		"""URL address of the main Yandex API server.
		@return: direct URL of Yandex API
		@rtype: str
		"""
		return self._directUrl

	@property
	def mirrorUrl(self) -> str:
		"""URL address of the alternative Yandex API server.
		@return: alternative URL of Yandex API
		@rtype: str
		"""
		return self._mirrorUrl

	@property
	def token(self) -> str:
		"""Yandex dictionary access token.
		@return: access token
		@rtype: str
		"""
		return secrets[serviceName].decode(config.conf[addonName][serviceName]['password'])

	def get(self, query: str) -> Dict:
		"""Request to the Yandex online dictionary using transmitted query.
		@param query: generated query URL not including domain name
		@type query: str
		@return: deserialized response from the online dictionary
		@rtype: Dict
		"""
		response, resp = {}, None
		servers = [self.directUrl, self.mirrorUrl]
		if self.mirror:
			servers.reverse()
		for server in servers:
			url = server + query
			rq = Request(url, method='GET', headers=self._headers)
			try:
				resp = urlopen(rq, timeout=8)
			except Exception as e:
				response['error'] = "HTTP error: %s [%s]" % (str(e), server)
				continue
			if resp.getcode() != 200:
				response['error'] = "Incorrect response code %d from the server %s" % (resp.getcode(), server)
				continue
			break
		if resp:
			stat['count'] = stat.get('count', 0) + 1
			try:
				response = loads(resp.read().decode(encoding='utf-8', errors='ignore'))
			except Exception as e:
				response['error'] = "JSON error: %s [%s]" % (str(e), server)
		return response

	def lookup(self) -> Dict:
		"""Get a dictionary article according to the specified parameters.
		@return: deserialized response from the online dictionary
		@rtype: Dict
		"""
		urlTemplate: str = "/api/v1/dicservice.json/lookup?{key}lang={lang}&text={text}{ui}"
		lang: str = "{lang1}-{lang2}".format(lang1=self.langFrom, lang2=self.langTo)
		query: str = urlTemplate.format(
			lang=lang,
			text=urlencode(self.text),
			key='key=%s&' % self.token,
			ui='&ui=%s' % self.uiLang or '')
		return self.get(query)

	def languages(self) -> Dict:
		"""Request for list of all languages available in the online dictionary.
		@return: deserialized response from the server
		@rtype: Dict
		"""
		urlTemplate: str = "/api/v1/dicservice.json/getLangs?key={key}"
		query: str = urlTemplate.format(key=self.token)
		return self.get(query)
