# api.py
# Provides interaction with the Yandex online dictionary API
# A part of the NVDA Quick Dictionary add-on
# This file is covered by the GNU General Public License.
# See the file COPYING for more details.
# Copyright (C) 2020-2026 Oleksandr Gryshchenko <grisov.nvaccess@mailgw.com>

import os.path
import ssl
from json import loads
from typing import Any
from urllib.parse import quote as urlencode
from urllib.request import Request, urlopen

from ..configuration import getAddonConfig
from ..service import secrets

# The certificates of the servers of the dictionary are not verified, as before, but only for the requests
# of this service: changing the default context of ssl would turn the verification off for all of NVDA
_sslContext = ssl.create_default_context()
_sslContext.check_hostname = False
_sslContext.verify_mode = ssl.CERT_NONE
serviceName: str = os.path.basename(os.path.dirname(__file__))
stat: dict[str, Any] = {}  # Object for store statistics


class Yapi(object):
	"""Description of the Yandex Online Dictionary API."""

	def __init__(
		self,
		text: str = "",
		langFrom: str = "",
		langTo: str = "",
		uiLang: str = "",
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
		super().__init__()
		self._directUrl: str = "https://dictionary.yandex.net"
		self._mirrorUrl: str = "https://info.alwaysdata.net"
		self._text = text
		self._langFrom = langFrom
		self._langTo = langTo
		self._uiLang = uiLang
		self._headers: dict[str, str] = {
			"User-Agent": "Mozilla 5.0",
		}

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
		return getAddonConfig()[serviceName]["mirror"]

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
		return secrets[serviceName].decode(getAddonConfig()[serviceName]["password"])

	def get(self, query: str) -> Any:
		"""Request to the Yandex online dictionary using transmitted query.
		@param query: generated query URL not including domain name
		@type query: str
		@return: deserialized response from the online dictionary, a dict with the "error" key if it has failed
		@rtype: Any
		"""
		response: Any = {}
		resp = None
		server = ""
		servers = [self.directUrl, self.mirrorUrl]
		if self.mirror:
			servers.reverse()
		for server in servers:
			url = server + query
			rq = Request(url, method="GET", headers=self._headers)
			try:
				resp = urlopen(rq, timeout=8, context=_sslContext)
			except Exception as e:
				response["error"] = "HTTP error: %s [%s]" % (str(e), server)
				continue
			if resp.status != 200:
				response["error"] = "Incorrect response code %d from the server %s" % (resp.status, server)
				continue
			break
		if resp:
			stat["count"] = stat.get("count", 0) + 1
			try:
				response = loads(resp.read().decode(encoding="utf-8", errors="ignore"))
			except Exception as e:
				response["error"] = "JSON error: %s [%s]" % (str(e), server)
		return response

	def lookup(self) -> dict[str, Any]:
		"""Get a dictionary article according to the specified parameters.
		@return: deserialized response from the online dictionary
		@rtype: dict[str, Any]
		"""
		urlTemplate: str = "/api/v1/dicservice.json/lookup?{key}lang={lang}&text={text}{ui}"
		lang: str = "{lang1}-{lang2}".format(lang1=self.langFrom, lang2=self.langTo)
		query: str = urlTemplate.format(
			lang=lang,
			text=urlencode(self.text),
			key="key=%s&" % self.token,
			ui="&ui=%s" % self.uiLang or "",
		)
		return self.get(query)

	def languages(self) -> Any:
		"""Request for list of all languages available in the online dictionary.
		@return: deserialized response from the server: the list of the language pairs or a dict with an error
		@rtype: Any
		"""
		urlTemplate: str = "/api/v1/dicservice.json/getLangs?key={key}"
		query: str = urlTemplate.format(key=self.token)
		return self.get(query)
