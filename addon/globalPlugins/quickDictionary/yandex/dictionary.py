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
import ssl
from urllib.request import Request, urlopen
from urllib.parse import quote as urlencode
from json import loads
import config
from .. import _addonName
from ..service import Translator, secrets
from ..shared import htmlTemplate
from .languages import langs


# Translators: The name of the online dictionary service
_serviceSummary = _("Yandex Dictionaries")
_serviceName = os.path.basename(os.path.dirname(__file__))
confspec = {
	"from": "string(default=%s)" % langs.defaultFrom.code,
	"into": "string(default=%s)" % langs.defaultInto.code,
	"autoswap": "boolean(default=false)",
	"copytoclip": "boolean(default=false)",
	"username": 'string(default="")',
	"password": "string(default=%s)" % secrets[_serviceName]._password,
	"mirror": "boolean(default=false)"
}
ssl._create_default_https_context = ssl._create_unverified_context


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
	uiLang = lambda self: self._langTo or langs.locale
	token = lambda self: secrets[_serviceName].decode(config.conf[_addonName][_serviceName]['password'])
	mirror = lambda self: config.conf[_addonName][_serviceName]['mirror']

	# Define class properties
	uiLang = property(uiLang)
	token = property(token)
	mirror = property(mirror)

	def run(self):
		"""Query the remote dictionary and save the processed response.
		Should run in a separate thread to avoid blocking.
		"""
		headers = {
			'User-Agent': 'Mozilla 5.0'}
		directUrl = 'https://dictionary.yandex.net'
		mirrorUrl = 'https://info.alwaysdata.net'
		servers = [directUrl, mirrorUrl]
		if self.mirror:
			servers.reverse()
		lang = '%s-%s' % (self.langFrom, self.langTo)
		urlTemplate = "{server}/api/v1/dicservice.json/lookup?{key}lang={lang}&text={text}{ui}"
		for server in servers:
			url = urlTemplate.format(server=server, lang=lang,
				text=urlencode(self.text),
				key = 'key=%s&' % self.token or '',
				ui = '&ui=%s' % self.uiLang or '')
			rq = Request(url, method='GET', headers=headers)
			try:
				resp = urlopen(rq, timeout=8)
			except Exception as e:
				log.error("%s, %s", str(e), server)
				self._html = 'Error: %s [%s]' % (str(e), server)
				continue
			if resp.status!=200:
				self._html = 'Error: incorrect response code %d from the server %s' % (resp.status, server)
				continue
			parser = Parser(loads(resp.read().decode()))
			html = parser.to_html()
			self._html = htmlTemplate.format(body=html) if html else html
			self._plaintext = parser.to_text()
			return


class Parser(object):
	"""Converts the response from the server into a human-readable formats.
	Must contain to_html() and to_text() methods.
	"""

	def __init__(self, resp:dict):
		"""Initializing input values.
		@param resp: response from server converted to dict format
		@type resp: dict
		"""
		self.resp = resp
		self.html = ''

	def attrs(self, resp:dict) -> str:
		"""Convert to string a sequence of attributes from fields:
		part of speech, number and gender.
		@param resp: part of the response from server converted to dict format
		@type resp: dict
		"""
		attrs = []
		for key in ["pos", "asp", "num", "gen"]:
			if key in resp:
				field = {
					# Translators: Field name in a dictionary entry
					'num': "<i>%s</i>: " % _("number"),
					# Translators: Field name in a dictionary entry
					'gen': "<i>%s</i>: " % _("gender")
					}.get(key, '') + resp[key]
				attrs.append(field)
		if attrs:
			return " (%s)" % ', '.join(attrs)
		return ''

	def to_html(self):
		"""Convert data received from a remote dictionary to HTML format."""
		if not isinstance(self.resp, dict): # incorrect response
			return ''
		if self.resp.get('message', None): # Error message
			return '<h1>%s</h1>' % self.resp['message']
		html = ''
		for key in ['def', 'tr', 'mean', 'syn', 'ex']:
			if key in self.resp:
				html += {
					# Translators: Field name in a dictionary entry
					'mean': "<p><i>%s</i>: " % _("mean").capitalize(),
					# Translators: Field name in a dictionary entry
					'syn': "<p><i>%s</i>:\n" % _("synonyms").capitalize(),
					# Translators: Field name in a dictionary entry
					'ex': "<p><i>%s</i>:\n" % _("examples").capitalize()
					}.get(key, '')
				if key == 'def':
					if not self.resp['def']:
						return ''
					for elem in self.resp['def']:
						html += '<h1>' + elem['text'] + self.attrs(elem) + '</h1>\n'
						html += Parser(elem).to_html()
						html += '\n'
				if key == 'tr':
					html += '<ul>\n'
					for elem in self.resp['tr']:
						html += '<li><b>' + elem['text'] + '</b>' + self.attrs(elem) + '\n'
						html += Parser(elem).to_html()
						html += '</li>\n';
					html += '</ul>\n'
				if key == 'mean':
					means = []
					for elem in self.resp['mean']:
						means.append(elem['text'] + self.attrs(elem) )
					html += ', '.join(means) + '</p>\n'
					del(means)
					html += Parser(elem).to_html()
				if key == 'syn':
					syns = []
					for elem in self.resp['syn']:
						syns.append(elem['text'] + self.attrs(elem))
					html += ', '.join(syns) + '</p>\n'
					del(syns)
					html += Parser(elem).to_html()
				if key == 'ex':
					exs = []
					for elem in self.resp['ex']:
						tmp = elem['text'] + self.attrs(elem)
						if 'tr' in elem:
							trs = []
							for extr in elem['tr']:
								trs.append(extr['text'] + self.attrs(extr))
							tmp += ' - ' + ', '.join(trs)
							del(trs)
						exs.append(tmp)
					html += ',\n'.join(exs) + '</p>'
					del(exs)
		self.html = html
		return self.html

	def to_text(self):
		"""Convert a dictionary response from HTML format to plain text."""
		li = u"\u2022 " # marker character code
		h1 = "- "
		text = self.html or self.to_html()
		text = text.replace('<li>', li).replace('<h1>', h1)
		text = re.sub(r'\<[^>]*\>', '', text)
		text = '\r\n'.join((s for s in text.split('\n') if s))
		return text
