#dictionary.py
# General object for executing translation requests
# the Translator class must be inherited by child ServiceTranslator classes
# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.
# See the file COPYING for more details.
# Copyright (C) 2020 Olexandr Gryshchenko <grisov.nvaccess@mailnull.com>

from logHandler import log
from threading import Thread, Event


class Translator(Thread):
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
		super(Translator, self).__init__(*args, **kwargs)
		self._stopEvent = Event()
		self._langFrom = langFrom
		self._langTo = langTo
		self._text = text
		self._html = ''
		self._plaintext = ''

	# The list of getters defining parameters for working with the dictionary
	langFrom = lambda self: self._langFrom
	langTo = lambda self: self._langTo
	text = lambda self: self._text
	html = lambda self: self._html
	plaintext = lambda self: self._plaintext

	# Define class properties
	langFrom = property(langFrom)
	langTo = property(langTo)
	text = property(text)
	html = property(html)
	plaintext = property(plaintext)

	def _stop(self, *args, **kwargs):
		"""Executed when a process terminates in a thread."""
		super(Translator, self)._stop(*args, **kwargs)
		self._stopEvent.set()

	def run(self):
		"""Query the remote dictionary and save the processed response.
		Should run in a separate thread to avoid blocking.
		"""
		raise NotImplementedError("This method must be overridden in the child class!")
