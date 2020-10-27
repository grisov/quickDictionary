#api.py
# Provides interaction with the Lexicala online dictionary API
# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.
# See the file COPYING for more details.
# Copyright (C) 2020 Olexandr Gryshchenko <grisov.nvaccess@mailnull.com>

import os
import ssl
import base64
from urllib.request import Request, urlopen
from urllib.parse import quote as urlencode
from json import loads
from datetime import datetime, timedelta
import config
from .. import _addonName
from ..service import secrets

ssl._create_default_https_context = ssl._create_unverified_context
serviceName = os.path.basename(os.path.dirname(__file__))
stat = {} # Object for store statistics


class Lapi(object):
	"""Description of the Lexicala Online Dictionary API."""

	def __init__(self, text:str='', lang:str='en', source:str='global', morph:bool=False, analyzed:bool=False):
		"""Input parameters for interacting with the online dictionary.
		@param text: word or phrase to search in the dictionary
		@type text: str
		@param lang: source search language
		@type lang: str
		@param source: data source in which the search will be performed
		@type source: str ("global", "password", "random")
		@param morph: searches for the text in both headwords and inflections, including in supplemental morphological lists
		@type morph: bool
		@param analyzed: algorithm that strips words to their stem, and disregards diacritics and case (uppercase/lowercase)
		@type analyzed:
		"""
		self._url = "https://dictapi.lexicala.com/"
		self._text = text
		self._lang = lang
		self._source = source
		self._morph = morph
		self._analyzed = analyzed
		self._headers = {
			'User-Agent': 'Mozilla 5.0'}

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
		@rtype: str ("global", "password", "random")
		"""
		return self._source

	@property
	def morph(self) -> bool:
		"""Option: searche for the text in both headwords and inflections, including in supplemental morphological lists.
		@return: whether option "morph" is enabled or disabled
		@rtype: bool
		"""
		return self._morph

	@property
	def analyzed(self) -> bool:
		"""Option: algorithm that strips words to their stem, and disregards diacritics and case (uppercase/lowercase).
		@return: whether option "analyzed" is enabled or disabled
		@rtype: bool
		"""
		return self._analyzed

	def get(self, query:str) -> dict:
		"""Request to the Lexicala online dictionary using transmitted query.
		@param query: generated query URL not including domain name
		@type query: str
		@return: deserialized response from the online dictionary
		@rtype: dict
		"""
		response, resp = {}, None
		url = self._url + query
		rq = Request(url)
		for name, value in self._headers.items():
			rq.add_header(name, value)
		base64string = base64.b64encode(bytes('%s:%s' % (
			secrets[serviceName].decode(config.conf[_addonName][serviceName]['username']),
			secrets[serviceName].decode(config.conf[_addonName][serviceName]['password'])
			), 'ascii'))
		rq.add_header("Authorization", "Basic %s" % base64string.decode('utf-8'))
		try:
			resp = urlopen(rq, timeout=8)
		except Exception as e:
			# e.getcode()==429 -> "To date, the number of allowed queries to the dictionary is exhausted!"
			response['error'] = "HTTP error: %s" % str(e)
			return response
		if resp:
			stat['remain'] = resp.getheader('X-RateLimit-DailyLimit-Remaining', 0)
			stat['count'] = int(resp.getheader('X-RateLimit-DailyLimit', 0)) - int(stat['remain'])
			stat['delta'] = datetime.now() - self.parseDate(resp.getheader('date', ''))
			if resp.getcode()==200:
				text = resp.read().decode(encoding='utf-8', errors='ignore')
				try:
					response = loads(text)
				except Exception as e:
					response['error'] = "JSON error: %s" % str(e)
			else:
				response['error'] = "Response code: %d" % resp.getcode()
		return response

	def search(self) -> dict:
		"""Request a word search in the online dictionary.
		@return: deserialized response from the server
		@rtype: dict
		"""
		query = "search?source={dictionary}&language={language}&text={text}&morph={morph}&analyzed={analyzed}".format(
			dictionary = self.source,
			language = self.language,
			text = urlencode(self.text),
			morph = str(self.morph).lower(),
			analyzed = str(self.analyzed).lower()
		)
		return self.get(query)

	def entries(self, id:str) -> dict:
		"""Request on a dictionary entry by its ID.
		@param id: identifier of a specific dictionary entry
		@type id: str
		@return: deserialized response from the server
		@rtype: dict
		"""
		query = "entries/{entry_id}".format(
			entry_id = id
		)
		return self.get(query)

	def senses(self, id:str) -> dict:
		"""Request on a dictionary entry for the specific sense of word by its ID.
		@param id: identifier of a dictionary entry for the specific sense of word
		@type id: str
		@return: deserialized response from the server
		@rtype: dict
		"""
		query = "senses/{sense_id}".format(
			sense_id = id
		)
		return self.get(query)

	def languages(self) -> dict:
		"""Request for lists of all languages available in the online dictionary.
		@return: deserialized response from the server
		@rtype: dict
		"""
		return self.get('languages')

	def test(self) -> dict:
		"""Check the functionality of the online dictionary API.
		Authorization is not required to fulfill this request.
		Also, this is not counted as a separate request in the daily quota of requests.
		@return: deserialized response from the server
		@rtype: dict
		"""
		return self.get('test')

	def parseDate(self, datestr:str) -> datetime:
		"""Analyze a date string and convert it to a datetime object.
		@param datestr: the date as a text string
		@type datestr: str
		@return: datetime object
		@rtype: datetime
		"""
		try:
			date = datestr.split(' ')[1:-1]
			date[1] = "%02d" % (['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'].index(date[1])+1)
			date = datetime.strptime(' '.join(date), "%d %m %Y %H:%M:%S")
		except Exception as e:
			return datetime.now() - timedelta(days=100)
		return date
