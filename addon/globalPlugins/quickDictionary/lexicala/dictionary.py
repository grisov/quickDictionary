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


class Parser(object):
	"""Parse the deserialized response from the server and returns it in HTML and text format."""

	def __init__(self, response:dict, target:str):
		"""Input data for further analysis and conversion to other formats.
		@param response: deserialized response from the online dictionary
		@type response: dict
		@param target: target language to search in the list of translations
		@type target: str
		"""
		self._resp = response
		self._langFrom = ''
		self._langInto = target
		self._html = ''

	def results(self) -> str:
		"""Analysis of the list of results.
		@return: all available results in HTML format
		@rtype: str
		"""
		if not self._resp.get('results') or len(self._resp['results'])==0:
			return self.error(self._resp)
		results = []
		for result in self._resp['results']:
			self._langFrom = self.language(result)
			transResp = Lapi().entries(self.id(result))
			results.append(self.headwords(transResp))
			results.append(self.senses(transResp))
		return '\n'.join(filter(lambda s: s!='', results))

	def headwords(self, resp:dict) -> str:
		"""Analysis of the "headword" object.
		Doc: "headword": object or list of objects
		@param resp: branch of the deserialized response from the server
		@type resp: dict
		@return: found data in HTML format
		@rtype: str
		"""
		rsp = resp.get('headword')
		if isinstance(rsp, list):
			hws = [self.headword(r) for r in rsp]
			return filter(lambda s: s!='', hws)
		return self.headword(rsp)

	def headword(self, resp:dict) -> str:
		"""Analysis of the "headword" list item.
		Doc: "headword": object (within the headwords array)
		@param resp: branch of the deserialized response from the server
		@type resp: dict
		@return: found data in HTML format
		@rtype: str
		"""
		if not resp or len(resp)==0:
			return ''
		hw = "<h1>%s</h1>" % (self.text(resp) + self.inParentheses(
			self.pos(resp),
			self.gender(resp),
			self.number(resp)))
		hw = [hw]
		hw.extend(self.filter(resp))
		return '\n'.join(filter(lambda s: s!='', hw))

	def senseIDs(self, resp:dict) -> list:
		"""Return a list of identifiers associated with the key "senses".
		@param resp: branch of the deserialized response from the server
		@type resp: dict
		@return: all found in current response branch dictionary article identifiers
		@rtype: list
		"""
		rsp = resp.get('senses')
		ids = []
		if isinstance(rsp, list):
			ids = [r['id'] for r in rsp if r.get('id')]
		return ids

	def senses(self, resp:dict) -> str:
		"""Analysis of the "senses" object.
		Doc: "senses": array of objects
		@param resp: branch of the deserialized response from the server
		@type resp: dict
		@return: found data in HTML format
		@rtype: str
		"""
		rsp = resp.get('senses')
		sns = ''
		if isinstance(rsp, list):
			sns = [self.withPrefix("<li>{value}</li>", '', self.sense(r)) for r in rsp]
			sns = filter(lambda s: s!='', sns)
			sns = '\n'.join(sns)
		else:
			sns = self.withPrefix("<li>{value}</li>", '', self.sense(rsp))
		return self.withPrefix('<ul type="disc">\n{value}\n</ul>', '', sns)

	def sense(self, resp:dict) -> str:
		"""Analysis of the "sense" object.
		Doc: "sense": object (within the senses array)
		@param resp: branch of the deserialized response from the server
		@type resp: dict
		@return: found data in HTML format
		@rtype: str
		"""
		if not resp or not isinstance(resp, dict):
			return ''
		sns = []
		#self.id(resp)
		sns.append(self.definition(resp) + self.translations(resp))
		sns.extend(self.filter(resp))
		sns = '\n'.join(filter(lambda s: s!='', sns))
		# Translators: Field name in a dictionary entry
		return self.withPrefix("<i>{name}</i>: {value}", _("mean"), sns)

	def compositional_phrases(self, resp:dict) -> str:
		"""Analysis of the "compositional_phrases" object.
		Doc: "compositional_phrases": array of objects
		@param resp: branch of the deserialized response from the server
		@type resp: dict
		@return: found data in HTML format
		@rtype: str
		"""
		rsp = resp.get('compositional_phrases')
		cp = ''
		if isinstance(rsp, list):
			cp = [self.withPrefix("<span>{value}</span>", '', self.compositional_phrase(r)) for r in rsp]
			cp = ', '.join(filter(lambda s: s!='', cp))
		else:
			cp = self.withPrefix("<span>{value}</span>", '', self.compositional_phrase(rsp))
		# Translators: Field name in a dictionary entry
		return self.withPrefix("<p><i>{name}</i>: {value}</p>", _("compositional phrases"), cp)

	def compositional_phrase(self, resp:dict) -> str:
		"""Analysis of the "compositional_phrase" object.
		Doc: "compositional_phrase": object (within the compositional_phrases array)
		@param resp: branch of the deserialized response from the server
		@type resp: dict
		@return: found data in HTML format
		@rtype: str
		"""
		if not resp or not isinstance(resp, dict):
			return ''
		cp = self.text(resp) + self.inParentheses(self.pos(resp))
		cp += self.withPrefix(" - {value}", '', self.definition(resp))
		cp = [cp]
		cp.extend(self.filter(resp))
		return '\n'.join(filter(lambda s: s and s!='', cp))

	def examples(self, resp:dict) -> str:
		"""Analysis of the "examples" array.
		Doc: "examples": array of objects
		@param resp: branch of the deserialized response from the server
		@type resp: dict
		@return: found data in HTML format
		@rtype: str
		"""
		rsp = resp.get('examples')
		exs = ''
		if isinstance(rsp, list):
			exs = [self.withPrefix("<span>{value}</span>", '', self.example(r)) for r in rsp]
			ex = filter(lambda s: s!='', exs)
			exs = ', '.join(exs)
		else:
			ex = self.withPrefix("<span>{value}</span>", '', self.example(rsp))
		# Translators: Field name in a dictionary entry
		return self.withPrefix("<p><i>{name}</i>: {value}</p>", _("examples"), exs)

	def example(self, resp:dict) -> str:
		"""Analysis of the "example" object.
		Doc: "example": object (within the examples array)
		@param resp: branch of the deserialized response from the server
		@type resp: dict
		@return: found data in HTML format
		@rtype: str
		"""
		if not resp or not isinstance(resp, dict):
			return ''
		example = [
			self.text(resp),
			self.alternative_scripts(resp)
		]
		return '\n'.join(filter(lambda s: s and s!='', example))

	def inflections(self, resp:dict) -> str:
		"""Analysis of the "inflections" object.
		Doc: "inflections": array of objects
		@param resp: branch of the deserialized response from the server
		@type resp: dict
		@return: found data in HTML format
		@rtype: str
		"""
		rsp = resp.get('inflections')
		ifs = ''
		if isinstance(rsp, list):
			ifs = [self.withPrefix("<span>{value}</span>", '', self.inflection(r)) for r in rsp]
			ifs = '\n'.join(filter(lambda s: s!='', ifs))
		else:
			ifs = self.withPrefix("<span>{value}</span>", '', self.inflection(rsp))
		# Translators: Field name in a dictionary entry
		return self.withPrefix("<p><i>{name}</i> {value}</p>", _("inflections"), ifs)

	def inflection(self, resp:dict) -> str:
		"""Analysis of the "inflection" object.
		Doc: "inflection": object (within the inflections array)
		@param resp: branch of the deserialized response from the server
		@type resp: dict
		@return: found data in HTML format
		@rtype: str
		"""
		if not resp or not isinstance(resp, dict):
			return ''
		inf = [
			resp.get('text') + self.inParentheses(
				self.pos(resp),
				self.gender(resp),
				self.number(resp))]
		inf.extend(self.filter(resp))
		return '\n'.join(filter(lambda s: s and s!='', inf))

	def pronunciation(self, resp:dict) -> str:
		"""Analysis of the "pronunciation" object.
		Doc: "pronunciation": object
		@param resp: branch of the deserialized response from the server
		@type resp: dict
		@return: found data in HTML format
		@rtype: str
		"""
		if not resp or not isinstance(resp, dict):
			return ''
		rsp = resp['pronunciation']
		pron = [
			rsp.get('value', ''),
			self.geographical_usage(rsp)
		]
		pron = ', '.join(filter(lambda s: s and s!='', pron))
		# Translators: Field name in a dictionary entry
		return self.withPrefix("<p><i>{name}</i> {value}</p>", _("pronunciation"), pron)

	def translations(self, resp:dict) -> str:
		"""Analysis of the "translations" object.
		Doc: "translations": object or array of objects
		@param resp: branch of the deserialized response from the server
		@type resp: dict
		@return: found data in HTML format
		@rtype: str
		"""
		rsp = resp.get('translations')
		if not rsp or not rsp.get(self._langInto) or len(rsp.get(self._langInto))==0:
			return ''
		rsp = rsp[self._langInto]
		trs = ''
		if isinstance(rsp, list):
			trs = [self.withPrefix("{value}", '', self.translation(r)) for r in rsp]
			trs = filter(lambda s: s!='', trs)
			trs = ', '.join(trs)
		else:
			trs = self.withPrefix("{value}", '', self.translation(rsp))
		return self.withPrefix(" - {value}", '', trs)

	def translation(self, resp:dict) -> str:
		"""Analysis of the "translations" list item object.
		Doc: "translation": object (within the translations array)
		@param resp: branch of the deserialized response from the server
		@type resp: dict
		@return: found data in HTML format
		@rtype: str
		"""
		trs = []
		trs.append(resp.get('text') + self.inParentheses(
			self.pos(resp),
			self.gender(resp),
			self.number(resp))
		)
		trs.extend(self.filter(resp))
		return '\n'.join(filter(lambda s: s!='', trs))

	def inParentheses(self, *args) -> str:
		"""List of values displayed in parentheses next to the word.
		@param args: strings to display
		@type args: list of str
		@return: if the input parameters are not empty - they are returned in parentheses
		@rtype: str
		"""
		fields = []
		for arg in args:
			if arg and arg.strip()!='':
				fields.append(str(arg))
		line = ', '.join(filter(lambda s: s!='', fields))
		return (" <i>(%s)</i>" % line) if line else ''

	def strList(self, resp) -> str:
		"""Convert an input str or list of strs to a single line.
		An argument can be either a string or a list of simple types.
		@return: line in which all input data are combined
		@rtype: str
		"""
		if isinstance(resp, list):
			return ', '.join(filter(lambda s: s and s!='', resp))
		elif resp and resp!='':
			return resp
		return ''

	def withPrefix(self, template:str, name:str, value:str) -> str:
		"""Display the field value after the specified prefix.
		Return an empty string if the last argument contains an empty value.
		The template must contain a {value} field and an optional {name} field.
		@return: combined in a str fields name and value according to the specified template
		@rtype: str
		"""
		if value and value!='':
			if '{name}' not in template:
				template += '{name}'
				name = ''
			return template.format(name=name.capitalize(), value=value)
		return ''

	def text(self, resp:dict) -> str:
		"""Get the value of the "text" field.
		Doc: "text": string
		@param resp: branch of the deserialized response from the server
		@type resp: dict
		@return: found data in HTML format
		@rtype: str
		"""
		return resp.get('text', '')

	def id(self, resp:dict) -> str:
		"""Get the value of the "id" field.
		Doc: "id": string
		@param resp: branch of the deserialized response from the server
		@type resp: dict
		@return: found data in HTML format
		@rtype: str
		"""
		return resp.get('id', '')

	def language(self, resp:dict) -> str:
		"""Get the value of the "language" field.
		Doc: "language": string
		@param resp: branch of the deserialized response from the server
		@type resp: dict
		@return: found data in HTML format
		@rtype: str
		"""
		return resp.get('language', '')

	def pos(self, resp:dict) -> str:
		"""Analysis of the "Part Of Speech" object.
		Doc: "pos": string or array of strings
		@param resp: branch of the deserialized response from the server
		@type resp: dict
		@return: found data in HTML format
		@rtype: str
		"""
		return self.strList(resp.get('pos'))

	def gender(self, resp:dict) -> str:
		"""Analysis of the "gender" object.
		Doc: "gender": string
		@param resp: branch of the deserialized response from the server
		@type resp: dict
		@return: found data in HTML format
		@rtype: str
		"""
		return self.strList(resp.get('gender'))

	def number(self, resp:dict) -> str:
		"""Get the value of the "number" field.
		Doc: "number": string
		@param resp: branch of the deserialized response from the server
		@type resp: dict
		@return: found data in HTML format
		@rtype: str
		"""
		return self.strList(resp.get('number'))

	def definition(self, resp:dict) -> str:
		"""Get the value of the "definition" field.
		Doc: "definition": string
		@param resp: branch of the deserialized response from the server
		@type resp: dict
		@return: found data in HTML format
		@rtype: str
		"""
		return resp.get('definition', '')

	def subcategorization(self, resp:dict) -> str:
		"""Get the value of the "subcategorization" field.
		Doc: "subcategorization": string or Array of strings
		@param resp: branch of the deserialized response from the server
		@type resp: dict
		@return: found data in HTML format
		@rtype: str
		"""
		# Translators: Field name in a dictionary entry
		return self.withPrefix("<p><i>{name}</i>: {value}</p>", _("subcategorization"), self.strList(resp.get('subcategorization')))

	def case(self, resp:dict) -> str:
		"""Get the value of the "case" field.
		Doc: "case": string or Array of strings
		@param resp: branch of the deserialized response from the server
		@type resp: dict
		@return: found data in HTML format
		@rtype: str
		"""
		# Translators: Field name in a dictionary entry
		return self.withPrefix("<p><i>{name}</i>: {value}</p>", _("case"), self.strList(resp.get('case')))

	def register(self, resp:dict) -> str:
		"""Get the value of the "register" field.
		Doc: "register": string or Array of strings
		@param resp: branch of the deserialized response from the server
		@type resp: dict
		@return: found data in HTML format
		@rtype: str
		"""
		# Translators: Field name in a dictionary entry
		return self.withPrefix("<p><i>{name}</i>: {value}</p>", _("register"), self.strList(resp.get('register')))

	def geographical_usage(self, resp:dict) -> str:
		"""Get the value of the "geographical_usage" field.
		Doc: "geographical_usage": string or Array of strings
		@param resp: branch of the deserialized response from the server
		@type resp: dict
		@return: found data in HTML format
		@rtype: str
		"""
		# Translators: Field name in a dictionary entry
		return self.withPrefix("<p><i>{name}</i>: {value}</p>", _("geographical usage"), self.strList(resp.get('geographical_usage')))

	def mood(self, resp:dict) -> str:
		"""Get the value of the "mood" field.
		Doc: "mood": string or Array of strings
		@param resp: branch of the deserialized response from the server
		@type resp: dict
		@return: found data in HTML format
		@rtype: str
		"""
		# Translators: Field name in a dictionary entry
		return self.withPrefix("<p><i>{name}</i>: {value}</p>", _("mood"), self.strList(resp.get('mood')))

	def tense(self, resp:dict) -> str:
		"""Get the value of the "tense" field.
		Doc: "tense": string or Array of strings
		@param resp: branch of the deserialized response from the server
		@type resp: dict
		@return: found data in HTML format
		@rtype: str
		"""
		# Translators: Field name in a dictionary entry
		return self.withPrefix("<p><i>{name}</i>: {value}</p>", _("tense"), self.strList(resp.get('tense')))

	def homograph_number(self, resp:dict) -> str:
		"""Get the value of the "homograph_number" field.
		Doc: "homograph_number": number
		@param resp: branch of the deserialized response from the server
		@type resp: dict
		@return: found data in HTML format
		@rtype: str
		"""
		# Translators: Field name in a dictionary entry
		return self.withPrefix("<p><i>{name}</i>: {value}</p>", _("homograph number"), self.strList(resp.get('homograph_number', '')))

	def alternative_scripts(self, resp:dict) -> str:
		"""Get the value of the "alternative_scripts" object.
		Doc: "alternative_scripts": object
		@param resp: branch of the deserialized response from the server
		@type resp: dict
		@return: found data in HTML format
		@rtype: str
		"""
		if isinstance(resp.get('alternative_scripts'), dict):
			return '\n'.join((self.withPrefix("{name}: {value}", key, val) for key, val in resp.get('alternative_scripts') if key!='' and val!=''))
		return ''

	def semantic_category(self, resp:dict) -> str:
		"""Analysis of the "semantic_category" object.
		Doc: "semantic_category": string or array of strings
		@param resp: branch of the deserialized response from the server
		@type resp: dict
		@return: found data in HTML format
		@rtype: str
		"""
		# Translators: Field name in a dictionary entry
		return self.withPrefix("<p><i>{name}</i>: {value}</p>", _("semantic category"), self.strList(resp.get('semantic_category')))

	def semantic_subcategory(self, resp:dict) -> str:
		"""Analysis of the "semantic_subcategory" object.
		Doc: "semantic_subcategory": string or array of strings
		@param resp: branch of the deserialized response from the server
		@type resp: dict
		@return: found data in HTML format
		@rtype: str
		"""
		# Translators: Field name in a dictionary entry
		return self.withPrefix("<p><i>{name}</i>: {value}</p>", _("semantic subcategory"), self.strList(resp.get('semantic_subcategory')))

	def range_of_application(self, resp:dict) -> str:
		"""Analysis of the "range_of_application" object.
		Doc: "range_of_application": string or array of strings
		@param resp: branch of the deserialized response from the server
		@type resp: dict
		@return: found data in HTML format
		@rtype: str
		"""
		# Translators: Field name in a dictionary entry
		return self.withPrefix("<p><i>{name}</i>: {value}</p>", _("range of application"), self.strList(resp.get('range_of_application')))

	def sentiment(self, resp:dict) -> str:
		"""Analysis of the "sentiment" object.
		Doc: "sentiment": string or array of strings
		@param resp: branch of the deserialized response from the server
		@type resp: dict
		@return: found data in HTML format
		@rtype: str
		"""
		# Translators: Field name in a dictionary entry
		return self.withPrefix("<p><i>{name}</i>: {value}</p>", _("sentiment"), self.strList(resp.get('sentiment')))

	def see(self, resp:dict) -> str:
		"""Analysis of the "see" object.
		Doc: "see": string or array of strings
		@param resp: branch of the deserialized response from the server
		@type resp: dict
		@return: found data in HTML format
		@rtype: str
		"""
		# Translators: Field name in a dictionary entry
		return self.withPrefix("<p><i>{name}</i>: {value}</p>", _("see"), self.strList(resp.get('see')))

	def see_also(self, resp:dict) -> str:
		"""Analysis of the "see_also" object.
		Doc: "see_also": string or array of strings
		@param resp: branch of the deserialized response from the server
		@type resp: dict
		@return: found data in HTML format
		@rtype: str
		"""
		# Translators: Field name in a dictionary entry
		return self.withPrefix("<p><i>{name}</i>: {value}</p>", _("see also"), self.strList(resp.get('see_also')))

	def synonyms(self, resp:dict) -> str:
		"""Analysis of the "synonyms" object.
		Doc: "synonyms": array of strings
		@param resp: branch of the deserialized response from the server
		@type resp: dict
		@return: found data in HTML format
		@rtype: str
		"""
		# Translators: Field name in a dictionary entry
		return self.withPrefix("<p><i>{name}</i>: {value}</p>", _("synonyms"), self.strList(resp.get('synonyms')))

	def antonyms(self, resp:dict) -> str:
		"""Analysis of the "antonyms" object.
		Doc: "antonyms": array of strings
		@param resp: branch of the deserialized response from the server
		@type resp: dict
		@return: found data in HTML format
		@rtype: str
		"""
		# Translators: Field name in a dictionary entry
		return self.withPrefix("<p><i>{name}</i>: {value}</p>", _("antonyms"), self.strList(resp.get('antonyms')))

	def collocate(self, resp:dict) -> str:
		"""Analysis of the "collocate" object.
		Doc: "collocate": array of strings
		@param resp: branch of the deserialized response from the server
		@type resp: dict
		@return: found data in HTML format
		@rtype: str
		"""
		# Translators: Field name in a dictionary entry
		return self.withPrefix("<p><i>{name}</i>: {value}</p>", _("collocate"), self.strList(resp.get('collocate')))

	def aspect(self, resp:dict) -> str:
		"""Get the value of the "aspect" field.
		Doc: "aspect": string
		@param resp: branch of the deserialized response from the server
		@type resp: dict
		@return: found data in HTML format
		@rtype: str
		"""
		# Translators: Field name in a dictionary entry
		return self.withPrefix("<p><i>{name}</i>: {value}</p>", _("aspect"), self.strList(resp.get('aspect')))

	def source(self, resp:dict) -> str:
		"""Get the value of the "source" field.
		Doc: "source": string
		@param resp: branch of the deserialized response from the server
		@type resp: dict
		@return: found data in HTML format
		@rtype: str
		"""
		# Translators: Field name in a dictionary entry
		return self.withPrefix("<p><i>{name}</i>: <b>{value}</b></p>", _("source dictionary"), resp.get('source', ''))

	def error(self, resp:dict) -> str:
		"""Convert errors received when connecting to the dictionary service into a text string.
		@param resp: branch of the deserialized response from the server
		@type resp: dict
		@return: found data in HTML format
		@rtype: str
		"""
		return self.withPrefix("<h1>{value}</h1>", "error", resp.get('error', ''))

	def filter(self, resp:dict) -> str:
		"""Passe the branch of the deserialized response  through a set of analyzers.
		@param resp: branch of the deserialized response from the server
		@type resp: dict
		@return: found data in HTML format
		@rtype: str
		"""
		return [
			#self.pronunciation(resp),
			self.subcategorization(resp),
			self.case(resp),
			self.mood(resp),
			self.register(resp),
			self.geographical_usage(resp),
			self.tense(resp),
			self.homograph_number(resp),
			self.inflections(resp),
			self.alternative_scripts(resp),
			self.collocate(resp),
			self.semantic_category(resp),
			self.semantic_subcategory(resp),
			self.range_of_application(resp),
			self.sentiment(resp),
			self.synonyms(resp),
			self.antonyms(resp),
			self.aspect(resp),
			self.senses(resp),
			self.compositional_phrases(resp),
			self.examples(resp),
			self.see(resp),
			self.see_also(resp),
		]

	def to_html(self) -> str:
		"""Return the HTML representation of the deserialized response sent to the class from the server.
		@return: found data in HTML format
		@rtype: str
		"""
		if not self._html:
			self._html = self.results().replace('\u02c8', '')
		return self._html

	def to_text(self) -> str:
		"""Convert a dictionary response from HTML format to plain text.
		@return: dictionary entry in text format
		@rtype: str
		"""
		li = u"\u2022 " # marker character code
		h1 = "- "
		text = self.to_html().replace('<li>', li).replace('<h1>', h1)
		text = re.sub(r'\<[^>]*\>', '', text)
		text = '\r\n'.join((s for s in text.split('\n') if s))
		return text
