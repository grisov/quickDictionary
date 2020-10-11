#shared.py
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

import re
import api
import ui
import braille
from speech import LangChangeCommand, CallbackCommand, speak
from textInfos import POSITION_SELECTION
from time import sleep
from tones import beep
from functools import lru_cache, wraps
import config
from .dictionary import Translator
from .synthesizers import profiles
from . import _addonName


@lru_cache(maxsize=100)
def translateWithCaching(langFrom: str, langInto: str, text: str) -> Translator:
	"""Call the request procedure to the remote server on a separate thread.
	Wait for the request to complete and return a prepared response.
	All function values are cached to reduce the number of requests to the server.
	@param langFrom: source language
	@type langFrom: str
	@param langInto: target language
	@type langInto: str
	@param text: word or phrase to translate
	@type text: str
	@return: object containing the prepared response from the remote dictionary
	@rtype: Translator
	"""
	translator = Translator(langFrom, langInto, text)
	translator.start()
	i=0
	while translator.is_alive():
		sleep(0.1)
		if i == 10:
			beep(500, 100)
			i = 0
		i+=1
	translator.join()
	return translator

def copyToClipboard(text: str):
	if api.copyToClip(text):
		# Translators: Message if the text was successfully copied to the clipboard
		ui.message(_("Copied to clipboard."))
	else:
		# Translators: Message if the text could not be copied to the clipboard
		ui.message(_("Copy failed."))

def getSelectedText() -> str:
	"""Retrieve the selected text.
	If the selected text is missing - extract the text from the clipboard.
	If the clipboard is empty or contains no text data - announce a warning.
	@return: selected text, text from the clipboard, or an empty string
	@rtype: str
	"""
	obj = api.getFocusObject()
	treeInterceptor = obj.treeInterceptor
	if hasattr(treeInterceptor, 'TextInfo') and not treeInterceptor.passThrough:
		obj = treeInterceptor
	try:
		info = obj.makeTextInfo(POSITION_SELECTION)
	except (RuntimeError, NotImplementedError):
		info = None
	if not info or info.isCollapsed or not clearText(info.text):
		try:
			text = api.getClipData()
		except Exception:
			text = ''
		if not text or not isinstance(text, str) or not clearText(text):
			# Translators: user has pressed the shortcut key for translating selected text, but no text was actually selected and clipboard is clear
			ui.message(_("There is no selected text, the clipboard is also empty, or its content is not text!"))
			return ''
		return clearText(text)
	return clearText(info.text)

def clearText(text: str) -> str:
	"""Retrieve only text information from a string, containing only letters and whitespace.
	@param text: incoming text string to be cleared of unnecessary characters
	@type text: str
	@return: text string stripped of unnecessary characters
	@rtype: str
	"""
	text = ''.join([s for s in text.strip() if s.isalpha() or s.isspace()])
	return ' '.join(re.split('\s+', text))

# Below toggle code came from Tyler Spivey's code, with enhancements by Joseph Lee (from Instant Translate add-on)
def finally_(func, final):
	"""Calls final after func, even if it fails."""
	def wrap(f):
		@wraps(f)
		def new(*args, **kwargs):
			try:
				func(*args, **kwargs)
			finally:
				final()
		return new
	return wrap(final)

# below function is taken from Instant Translate add-on
def messageWithLangDetection(msg: dict):
	"""Pronounce text in a given language,
	if enabled the setting for auto-switching languages of the synthesizer.
	@param msg: language code and text to be spoken in the specified language
	@type msg: dict -> {'lang': str, 'text': str}
	"""
	speechSequence=[]
	if config.conf['speech']['autoLanguageSwitching']:
		speechSequence.append(LangChangeCommand(msg['lang']))
	speechSequence.append(msg['text'])
	if config.conf[_addonName]['switchsynth']:
		speechSequence.append(CallbackCommand(callback=profiles.restoreDefault))
	speak(speechSequence)
	braille.handler.message(msg['text'])
