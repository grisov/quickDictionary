# dictionary.py
# Service summary, configuration scheme and objects for executing translation requests
# and processing the received responses
# A part of the NVDA Quick Dictionary add-on
# This file is covered by the GNU General Public License.
# See the file COPYING for more details.
# Copyright (C) 2020-2021 Olexandr Gryshchenko <grisov.nvaccess@mailnull.com>

from typing import Callable, List, Dict
import addonHandler
from logHandler import log
from ..service import Translator, Parser, secrets
from ..shared import htmlTemplate
from .api import serviceName, Yapi
from .languages import langs

try:
	addonHandler.initTranslation()
except addonHandler.AddonError:
	log.warning("Unable to init translations. This may be because the addon is running from NVDA scratchpad.")
_: Callable[[str], str]


# Translators: The name of the online dictionary service
serviceSummary = _("Yandex Dictionaries")

confspec = {
	"from": "string(default=%s)" % langs.defaultFrom.code,
	"into": "string(default=%s)" % langs.defaultInto.code,
	"autoswap": "boolean(default=false)",
	"copytoclip": "boolean(default=false)",
	"username": 'string(default="")',
	"password": "string(default=%s)" % secrets[serviceName]._password,
	"mirror": "boolean(default=false)",
	"switchsynth": "boolean(default=false)"
}


class ServiceTranslator(Translator):
	"""Provides interaction with the online dictionary service."""

	def __init__(
		self,
		langFrom: str,
		langTo: str,
		text: str,
		*args, **kwargs
	) -> None:
		"""Initialization of the source and target language, as well as word or phrase to search in the dictionary.
		@param langFrom: source language
		@type langFrom: str
		@param langTo: target language
		@type langTo: str
		@param text: a word or phrase to look up in a dictionary
		@type text: str
		"""
		super(ServiceTranslator, self).__init__(langFrom, langTo, text, *args, **kwargs)

	@property
	def uiLang(self) -> str:
		"""User interface language which will be used to display labels.
		@return: UI language code
		@rtype: str
		"""
		return self._langTo or langs.locale.code

	def run(self) -> None:
		"""Query the remote dictionary and save the processed response.
		Should run in a separate thread to avoid blocking.
		"""
		self._resp = Yapi(
			text=self.text,
			langFrom=self.langFrom,
			langTo=self.langTo,
			uiLang=self.uiLang
		).lookup()
		if self._resp.get('error'):
			self._error = True
		parser: Parser = ServiceParser(self._resp)
		html: str = parser.to_html()
		self._html = htmlTemplate.format(body=html) if html else html
		self._plaintext = parser.to_text()


class ServiceParser(Parser):
	"""Converts the response from the server into a human-readable formats.
	Must contain to_html() and to_text() methods.
	"""

	def attrs(self, resp: Dict[str, str]) -> str:
		"""Convert to string a sequence of attributes from fields:
		part of speech, number and gender.
		@param resp: part of the response from server converted to dict format
		@type resp: Dict[str, str]
		"""
		attrs: List[str] = []
		for key in ["pos", "asp", "num", "gen"]:
			if key in resp:
				field: str = {
					# Translators: Field name in a dictionary entry
					'num': "<i>%s</i>: " % _("number"),
					# Translators: Field name in a dictionary entry
					'gen': "<i>%s</i>: " % _("gender")
				}.get(key, '') + resp[key]
				attrs.append(field)
		if attrs:
			return " (%s)" % ', '.join(attrs)
		return ''

	def to_html(self) -> str:  # noqa C901
		"""Convert data received from a remote dictionary to HTML format.
		@return: converted to HTML deserialized response from server
		@rtype: str
		"""
		if not isinstance(self.resp, dict):  # incorrect response
			return ''
		if self.resp.get('error', ''):  # Error message
			return '<h1>%s</h1>' % self.resp['error']
		html: str = ''
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
						html += ServiceParser(elem).to_html()
						html += '\n'
				if key == 'tr':
					html += '<ul>\n'
					for elem in self.resp['tr']:
						html += '<li><b>' + elem['text'] + '</b>' + self.attrs(elem) + '\n'
						html += ServiceParser(elem).to_html()
						html += '</li>\n'
					html += '</ul>\n'
				if key == 'mean':
					means = []
					for elem in self.resp['mean']:
						means.append(elem['text'] + self.attrs(elem))
					html += ', '.join(means) + '</p>\n'
					del(means)
					html += ServiceParser(elem).to_html()
				if key == 'syn':
					syns = []
					for elem in self.resp['syn']:
						syns.append(elem['text'] + self.attrs(elem))
					html += ', '.join(syns) + '</p>\n'
					del(syns)
					html += ServiceParser(elem).to_html()
				if key == 'ex':
					exs: List[str] = []
					for elem in self.resp['ex']:
						tmp = elem['text'] + self.attrs(elem)
						if 'tr' in elem:
							trs: List[str] = []
							for extr in elem['tr']:
								trs.append(extr['text'] + self.attrs(extr))
							tmp += ' - ' + ', '.join(trs)
							del(trs)
						exs.append(tmp)
					html += ',\n'.join(exs) + '</p>'
					del(exs)
		self.html = html
		return self.html
