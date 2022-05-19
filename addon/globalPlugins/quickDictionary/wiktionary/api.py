# api.py
# Provides interaction with the Wiktionary online dictionary API
# Documentation: https://en.wiktionary.org/w/api.php
# A part of the NVDA Quick Dictionary add-on
# This file is covered by the GNU General Public License.
# See the file COPYING for more details.
# Copyright (C) 2020-2021 Olexandr Gryshchenko <grisov.nvaccess@mailnull.com>

from typing import Any, Dict
import os.path
import ssl
from urllib.request import Request, urlopen
from urllib.parse import quote as urlencode
from json import loads

ssl._create_default_https_context = ssl._create_unverified_context
serviceName: str = os.path.basename(os.path.dirname(__file__))
stat: Dict[str, Any] = {}  # Object for store statistics


class Wapi(object):
	"""Description of the Wiktionary Online Dictionary API."""

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
		self._url: str = "https://{lang}.wiktionary.org/w/api.php"
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
		return self._uiLang or self.langTo or "en"

	@property
	def url(self) -> str:
		"""URL address of the Wiktionary API server.
		@return: direct URL of Wiktionary API
		@rtype: str
		"""
		return self._url

	def get(self, query: str) -> Dict:
		"""Request to the Wiktionary online dictionary using transmitted query.
		@param query: generated query URL without API URL
		@type query: str
		@return: deserialized response from the online dictionary
		@rtype: Dict
		"""
		response, resp = {}, None
		url: str = f"{self.url}?{query}".format(lang=self.uiLang)
		rq = Request(url, method='GET', headers=self._headers)
		try:
			resp = urlopen(rq, timeout=8)
		except Exception as e:
			response['error'] = "HTTP error: %s [%s]" % (str(e), self.url)
		self.resp = resp
		if getattr(resp, "getcode")() != 200:
			response['error'] = "Incorrect response code %d from the server %s" % (
				getattr(resp, "getcode")(),
				self.url)
		if resp:
			stat['count'] = stat.get('count', 0) + 1
			try:
				response = loads(resp.read().decode(encoding='utf-8', errors='ignore'))
			except Exception as e:
				response['error'] = "JSON error: %s [%s]" % (str(e), self.url)
		return response

	def languages(self) -> Dict:
		"""Request for list of all languages available in the online dictionary.
		@return: deserialized response from the server
		@rtype: Dict
		"""
		query: str = "action=query&meta=siteinfo&siprop=languages&format=json"
		response: Dict = self.get(query)
		return response.get('query', {}) or response

	def lookup(self) -> Dict:
		query: str = "action=query&format=json&prop=extracts&uselang={lang}&titles={text}".format(
			lang=self.langTo,
			text=urlencode(self.text)
		)
		# prop=extracts
		return self.get(query)

# from globalPlugins.quickDictionary.wiktionary.api import Wapi
