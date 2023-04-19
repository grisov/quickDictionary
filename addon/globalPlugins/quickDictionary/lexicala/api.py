# api.py
# Provides interaction with the Lexicala online dictionary API
# A part of the NVDA Quick Dictionary add-on
# This file is covered by the GNU General Public License.
# See the file COPYING for more details.
# Copyright (C) 2020-2023 Olexandr Gryshchenko <grisov.nvaccess@mailnull.com>

from typing import Any, Dict, List, Optional
import os.path
import ssl
import base64
from urllib.request import Request, urlopen
from urllib.parse import quote as urlencode
from http.client import HTTPResponse
from json import loads
from datetime import datetime, timedelta
import config
from .. import addonName
from ..service import secrets

ssl._create_default_https_context = ssl._create_unverified_context
serviceName: str = os.path.basename(os.path.dirname(__file__))
stat: Dict[str, Any] = {}  # Object for store statistics


class Lapi(object):
	"""Description of the Lexicala Online Dictionary API."""

	def __init__(
		self,
		text: str = '',
		lang: str = 'en',
		source: str = 'global',
		# Starting with Python 3.8 is better to use here: Literal["global", "password", "random"]
		morph: bool = False,
		analyzed: bool = False
	) -> None:
		"""Input parameters for interacting with the online dictionary.
		@param text: word or phrase to search in the dictionary
		@type text: str
		@param lang: source search language
		@type lang: str
		@param source: data source in which the search will be performed
		@type source: str
			starting with Python 3.8 is better to use Literal["global", "password", "random"]
		@param morph: searches for the text in both headwords and inflections,
			including in supplemental morphological lists
		@type morph: bool
		@param analyzed: algorithm that strips words to their stem,
			and disregards diacritics and case (uppercase/lowercase)
		@type analyzed: bool
		"""
		self._url: str = "https://lexicala1.p.rapidapi.com/"
		self._text = text
		self._lang = lang
		self._source = source
		self._morph = morph
		self._analyzed = analyzed
		self._headers: Dict[str, str] = {
			"X-RapidAPI-Host": "lexicala1.p.rapidapi.com",
			"User-Agent": "Mozilla 5.0"
		}

	@property
	def text(self) -> str:
		"""Word or phrase to search in the dictionary.
		@return: the value of the text field
		@rtype: str
		"""
		return self._text

	@property
	def language(self) -> str:
		"""Source search language.
		@return: the value of the language field
		@rtype: str
		"""
		return self._lang

	@property
	def source(self) -> str:
		"""Data source in which the search will be performed.
		@return: the name of the data source in which the search will be performed
		@rtype: Literal["global", "password", "random"]
		"""
		return self._source

	@property
	def morph(self) -> bool:
		"""Option: searche for the text in both headwords and inflections,
		including in supplemental morphological lists.
		@return: whether option "morph" is enabled or disabled
		@rtype: bool
		"""
		return self._morph

	@property
	def analyzed(self) -> bool:
		"""Option: algorithm that strips words to their stem,
		and disregards diacritics and case (uppercase/lowercase).
		@return: whether option "analyzed" is enabled or disabled
		@rtype: bool
		"""
		return self._analyzed

	def get(self, query: str) -> Dict:
		"""Request to the Lexicala online dictionary using transmitted query.
		@param query: generated query URL not including domain name
		@type query: str
		@return: deserialized response from the online dictionary
		@rtype: Dict
		"""
		response: Dict = {}
		resp: Optional[HTTPResponse] = None
		url: str = self._url + query
		rq = Request(url)
		for name, value in self._headers.items():
			rq.add_header(name, value)
		rq.add_header("X-RapidAPI-Key", secrets[serviceName].decode(config.conf[addonName][serviceName]['password']))
		try:
			resp = urlopen(rq, timeout=8)
		except Exception as e:
			# e.getcode()==429 -> "To date, the number of allowed queries to the dictionary is exhausted!"
			response['error'] = "HTTP error: %s" % str(e)
			return response
		if resp:
			stat['remain'] = resp.getheader("X-RateLimit-requests-Remaining", 0)
			stat['count'] = int(resp.getheader("X-RateLimit-requests-Limit", 0)) - int(stat['remain'])
			stat['delta'] = datetime.now() - self.parseDate(resp.getheader('date', ''))
			if resp.getcode() == 200:
				text: str = resp.read().decode(encoding='utf-8', errors='ignore')
				try:
					response = loads(text)
				except Exception as e:
					response['error'] = "JSON error: %s" % str(e)
			else:
				response['error'] = "Response code: %d" % resp.getcode()
		return response

	def search(self) -> Dict:
		"""Request a word search in the online dictionary.
		@return: deserialized response from the server
		@rtype: Dict
		"""
		query: str = "search?source={dict}&language={lang}&text={text}&morph={morph}&analyzed={analyzed}".format(
			dict=self.source,
			lang=self.language,
			text=urlencode(self.text),
			morph=str(self.morph).lower(),
			analyzed=str(self.analyzed).lower()
		)
		return self.get(query)

	def entries(self, id: str) -> Dict:
		"""Request on a dictionary entry by its ID.
		@param id: identifier of a specific dictionary entry
		@type id: str
		@return: deserialized response from the server
		@rtype: Dict
		"""
		query: str = "entries/{entry_id}".format(
			entry_id=id
		)
		return self.get(query)

	def senses(self, id: str) -> Dict:
		"""Request on a dictionary entry for the specific sense of word by its ID.
		@param id: identifier of a dictionary entry for the specific sense of word
		@type id: str
		@return: deserialized response from the server
		@rtype: Dict
		"""
		query: str = "senses/{sense_id}".format(
			sense_id=id
		)
		return self.get(query)

	def languages(self) -> Dict:
		"""Request for lists of all languages available in the online dictionary.
		@return: deserialized response from the server
		@rtype: Dict
		"""
		return self.get('languages')

	def test(self) -> Dict:
		"""Check the functionality of the online dictionary API.
		Authorization is not required to fulfill this request.
		Also, this is not counted as a separate request in the daily quota of requests.
		@return: deserialized response from the server
		@rtype: Dict
		"""
		return self.get('test')

	def parseDate(self, datestr: str) -> datetime:
		"""Analyze a date string and convert it to a datetime object.
		@param datestr: the date as a text string
		@type datestr: str
		@return: datetime object
		@rtype: datetime
		"""
		monthes: List[str] = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
		try:
			date = datestr.split(' ')[1:-1]
			date[1] = "%02d" % (monthes.index(date[1]) + 1)
			dt: datetime = datetime.strptime(' '.join(date), "%d %m %Y %H:%M:%S")
		except Exception:
			return datetime.now() - timedelta(days=100)
		return dt
