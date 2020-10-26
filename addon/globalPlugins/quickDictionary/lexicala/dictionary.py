#dictionary.py
# Service summary, configuration scheme and objects for executing translation requests and processing the received answers
# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.
# See the file COPYING for more details.
# Copyright (C) 2020 Olexandr Gryshchenko <grisov.nvaccess@mailnull.com>

import addonHandler
from logHandler import log
try:
	addonHandler.initTranslation()
except addonHandler.AddonError:
	log.warning("Unable to initialise translations. This may be because the addon is running from NVDA scratchpad.")

import os
import re
import json
import ssl
from urllib import request
from urllib.parse import quote as urlencode
import base64
import config
from .. import _addonName
from ..service import Translator, secrets
from ..shared import htmlTemplate
from .languages import langs


# Translators: The name of the online dictionary service
_serviceSummary = _("Lexicala Dictionaries")
_serviceName = os.path.basename(os.path.dirname(__file__))
confspec = {
	"from": "string(default=%s)" % langs.defaultFrom.code,
	"into": "string(default=%s)" % langs.defaultInto.code,
	"source": "string(default=%s)" % 'password',
	"autoswap": "boolean(default=false)",
	"copytoclip": "boolean(default=false)",
	"username": 'string(default=%s)' % secrets[_serviceName]._username,
	"password": "string(default=%s)" % secrets[_serviceName]._password,
	"morph": "boolean(default=false)",
	"analyzed": "boolean(default=false)"
}
ssl._create_default_https_context = ssl._create_unverified_context


h = {} # Temporary object

class ServiceTranslator(Translator):
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
		super(ServiceTranslator, self).__init__(langFrom, langTo, text, *args, **kwargs)

	# The list of getters defining parameters for working with the dictionary
	source = lambda self: config.conf[_addonName][_serviceName]['source']
	morph = lambda self: config.conf[_addonName][_serviceName]['morph']
	analyzed = lambda self: config.conf[_addonName][_serviceName]['analyzed']

	# Define class properties
	source = property(source)
	morph = property(morph)
	analyzed = property(analyzed)

	def run(self):
		"""Query the remote dictionary and save the processed response.
		Should run in a separate thread to avoid blocking.
		"""
		resp = Lapi(text=self.text, lang=self.langFrom, source=self.source, morph=self.morph, analyzed=self.analyzed).search()
		parser = Parser(response=resp, target=self.langTo)
		html = parser.to_html()
		self._html = htmlTemplate.format(body=html) if html else html
		self._plaintext = parser.to_text()
		return


class Lapi(object):
	"""Description of the Lexicala Online Dictionary API."""

	def __init__(self, text:str='', lang:str='en', source:str='password', morph:bool=False, analyzed:bool=False):
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
		response = {}
		url = self._url + query
		rq = request.Request(url)
		for name, value in self._headers.items():
			rq.add_header(name, value)
		base64string = base64.b64encode(bytes('%s:%s' % (
			secrets[_serviceName].decode(config.conf[_addonName][_serviceName]['username']),
			secrets[_serviceName].decode(config.conf[_addonName][_serviceName]['password'])), 'ascii'))
		rq.add_header("Authorization", "Basic %s" % base64string.decode('utf-8'))
		try:
			resp = request.urlopen(rq, timeout=8)
		except Exception as e:
			if e.getcode()==429:
				# Translators: Notification when the request limit to the server is exhausted
				response['error'] = _("To date, the number of allowed queries to the dictionary is exhausted!")
			response['error'] = str(e)
			return response
		h['limit'] = resp.getheader('X-RateLimit-DailyLimit')
		h['remain'] = resp.getheader('X-RateLimit-DailyLimit-Remaining')
		#h['date'] = datefstr(resp.getheader('date'))
		#h['tomiddle'] = remains(h['date'])
		if resp.getcode()==200:
			text = resp.read().decode(encoding='utf-8', errors='ignore')
			response = json.loads(text)
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
