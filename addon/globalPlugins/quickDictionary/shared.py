# shared.py
# Some functions for different purposes at the add-on level
# A part of the NVDA Quick Dictionary add-on
# This file is covered by the GNU General Public License.
# See the file COPYING for more details.
# Copyright (C) 2020-2026 Oleksandr Gryshchenko <grisov.nvaccess@mailgw.com>

import os.path
import re
from collections.abc import Callable
from functools import lru_cache, wraps
from threading import Thread
from time import sleep
from typing import Any, cast

import addonHandler
import api
import braille
import speech
import ui
from logHandler import log
from speech.commands import CallbackCommand, LangChangeCommand
from speech.types import SpeechSequence
from textInfos import POSITION_SELECTION
from tones import beep

from .configuration import getAddonConfig, getNvdaConfig
from .locator import getActiveService, services
from .service import Translator
from .synthesizers import profiles

try:
	addonHandler.initTranslation()
except addonHandler.AddonError:
	log.warning("Unable to init translations. This may be because the addon is running from NVDA scratchpad.")
_: Callable[[str], str]


@lru_cache(maxsize=64)
def translateWithCaching(langFrom: str, langInto: str, text: str, hashForCache: int) -> Translator:
	"""Call the request procedure to the remote server on a separate thread.
	Wait for the request to complete and return a prepared response.
	All function values are cached to reduce the number of requests to the server.
	@param langFrom: source language
	@type langFrom: str
	@param langInto: target language
	@type langInto: str
	@param text: word or phrase to translate
	@type text: str
	* this parameter is not used in the function, but is required for to properly caching
	@param hashForCache: hash of all parameters that must be considered when caching
	@type hashForCache: int
	@return: object containing the prepared response from the remote dictionary
	@rtype: Translator
	"""
	translator = getActiveService().translator(langFrom, langInto, text)
	translator.start()
	i = 0
	while translator.is_alive():
		sleep(0.1)
		if i == 10:
			beep(500, 100)
			i = 0
		i += 1
	translator.join()
	return translator


def hashForCache(active: int) -> int:
	"""Hash sum of the values of all service parameters that must be taken into account when caching requests."""
	hashes: int = active
	for value in getAddonConfig()[services[active].name].values():
		hashes += hash(value)
	return hashes


def waitingFor(target: Callable[..., Any], args: tuple[Any, ...] = ()) -> None:
	"""Waiting for the function to complete, beeps are output while waiting.
	@param target: function that will be started and user will hear sounds during its execution
	@type target: Callable[..., Any]
	@param args: arguments to be passed to the function
	@type args: tuple[Any, ...]
	"""
	load = Thread(target=target, args=args)
	load.start()
	i = 0
	while load.is_alive():
		sleep(0.1)
		if i == 10:
			beep(500, 100)
			i = 0
		i += 1
	load.join()


def getSelectedText() -> str:
	"""Retrieve the selected text.
	If the selected text is missing - extract the text from the clipboard.
	If the clipboard is empty or contains no text data - announce a warning.
	@return: selected text, text from the clipboard, or an empty string
	@rtype: str
	"""
	# The focus objects and the tree interceptors of NVDA have incomplete type annotations
	obj: Any = api.getFocusObject()
	treeInterceptor: Any = obj.treeInterceptor
	if hasattr(treeInterceptor, "TextInfo") and not treeInterceptor.passThrough:
		obj = treeInterceptor
	info: Any = None
	try:
		info = obj.makeTextInfo(POSITION_SELECTION)
	except (RuntimeError, NotImplementedError):
		pass
	if not info or info.isCollapsed or not clearText(info.text):
		try:
			text = api.getClipData()
		except Exception:
			text = ""
		if not text or not clearText(text):
			# Translators: User has pressed the shortcut key for translating selected text,
			# but no text was actually selected and clipboard is clear
			ui.message(
				_("There is no selected text, the clipboard is also empty, or its content is not text!"),
			)
			return ""
		return text
	return str(info.text)


def clearText(text: str) -> str:
	"""Retrieve only text information from a string, containing only letters and whitespace.
	@param text: incoming text string to be cleared of unnecessary characters
	@type text: str
	@return: text string stripped of unnecessary characters
	@rtype: str
	"""
	text = "".join([s for s in text.strip() if s.isalpha() or s.isspace()])
	return " ".join(re.split(r"\s+", text))


# Below toggle code came from Tyler Spivey's code, with enhancements by Joseph Lee
def finally_(func: Callable[..., Any], final: Callable[[], Any]) -> Callable[..., None]:
	"""Calls final after func, even if it fails.
	@param func: the function to call
	@type func: Callable[..., Any]
	@param final: the function called after func
	@type final: Callable[[], Any]
	@return: the function that calls both
	@rtype: Callable[..., None]
	"""

	def wrap(f: Callable[[], Any]) -> Callable[..., None]:
		@wraps(f)
		def new(*args: Any, **kwargs: Any) -> None:
			try:
				func(*args, **kwargs)
			finally:
				final()

		return new

	return wrap(final)


# Template for displaying HTML content.
htmlTemplate = "".join(
	[
		"&nbsp;",
		"<!DOCTYPE html>",
		"<html>",
		"<head>",
		'<meta http-equiv="Content-Type" content="text/html; charset=utf-8">',
		"<title></title>",
		'<link rel="stylesheet" type="text/css" href="%s">'
		% os.path.join(os.path.dirname(__file__), "style.css"),
		"</head>",
		"<body>{body}</body>",
		"</html>",
	],
)


def restoreSynthIfSpeechBeenCanceled() -> None:
	"""Restore the previous voice synthesizer if speech is canceled or finished.
	Must be run in a separate thread which will control the main process.
	"""
	previous = profiles.getCurrent()
	while not getattr(speech.getState(), "beenCanceled", False):
		sleep(0.1)
	_ = profiles.restorePrevious()
	_ = profiles.rememberCurrent(previous)


def messageWithLangDetection(msg: dict[str, str]) -> None:
	"""Pronounce text in a given language if enabled the setting for auto-switching languages of the synthesizer.
	After the speech, switche to the previous synthesizer, if the corresponding option is enabled.
	@param msg: language code and text to be spoken in the specified language
	@type msg: dict[str, str] -> {'lang': str, 'text': str}
	"""
	switchSynth = getAddonConfig()[getActiveService().name]["switchsynth"]
	profile = next((p for _slot, p in profiles if p.lang == msg["lang"]), None)
	if switchSynth and profile:
		_ = profiles.rememberCurrent()
		_ = profile.set()
	speechSequence: SpeechSequence = []
	if getNvdaConfig()["speech"]["autoLanguageSwitching"]:
		speechSequence.append(LangChangeCommand(msg["lang"]))
	if switchSynth and profile:
		speechSequence.append(CallbackCommand(callback=Thread(target=restoreSynthIfSpeechBeenCanceled).start))
	speechSequence.append(msg["text"])
	if switchSynth and profile:
		speechSequence.append(CallbackCommand(callback=speech.cancelSpeech))
	speech.speak(speechSequence)
	# braille.handler is None only until braille has been initialized
	cast(Any, braille.handler).message(msg["text"])
