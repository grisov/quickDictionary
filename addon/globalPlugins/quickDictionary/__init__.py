#-*- coding:utf-8 -*-
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
_addonDir = os.path.join(os.path.dirname(__file__), "..", "..")
if isinstance(_addonDir, bytes):
	_addonDir = _addonDir.decode("mbcs")
_curAddon = addonHandler.Addon(_addonDir)
_addonName = _curAddon.manifest['name']
_addonSummary = _curAddon.manifest['summary']

import globalPluginHandler
from scriptHandler import script
from queueHandler import queueFunction, eventQueue
import api, ui, config
import gui, wx
from tones import beep
from threading import Thread
from .shared import copyToClipboard, getSelectedText, translateWithCaching, messageWithLangDetection, finally_
from .languages import langs
from .synthesizers import profiles
from .settings import QuickDictionarySettingsPanel
from .secret import APIKEY as TOKEN


class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	"""Implementation global commands of NVDA add-on"""
	scriptCategory = str(_addonSummary)

	def __init__(self, *args, **kwargs):
		"""Initializing initial configuration values ​​and other fields"""
		super(GlobalPlugin, self).__init__(*args, **kwargs)
		confspec = {
			"from": "string(default=%s)" % langs.defaultFrom,
			"into": "string(default=%s)" % langs.defaultInto,
			"autoswap": "boolean(default=false)",
			"copytoclip": "boolean(default=false)",
			"switchsynth": "boolean(default=true)",
			"token": "string(default=%s)" % TOKEN,
			"mirror": "boolean(default=false)"
		}
		config.conf.spec[_addonName] = confspec
		gui.settingsDialogs.NVDASettingsDialog.categoryClasses.append(QuickDictionarySettingsPanel)
		# to use the second layer of keyboard shortcuts
		self._toggleGestures = False
		# to use copy latest translation to the clipboard
		self._lastTranslator = None
		# to use speech synthesizers profiles
		self._slot = 1

	@property
	def source(self) -> str:
		"""Source language for translation.
		@return: usually two-character language code
		@rtype: str
		"""
		return config.conf[_addonName]['from']

	@source.setter
	def source(self, lang: str):
		"""Setter for source language.
		@param lang: usually two-character language code
		@type lang: str
		"""
		config.conf[_addonName]['from'] = lang

	@property
	def target(self) -> str:
		"""Target language for translation.
		@return: usually two-character language code
		@rtype: str
		"""
		return config.conf[_addonName]['into']

	@target.setter
	def target(self, lang: str):
		"""Setter for target language.
		@param lang: usually two-character language code
		@type lang: str
		"""
		config.conf[_addonName]['into'] = lang

	@property
	def isCopyToClipboard(self) -> bool:
		"""Property specifying whether to copy the dictionary results to the clipboard each time.
		@return: value stored in the add-on configuration
		@rtype: bool
		"""
		return config.conf[_addonName]['copytoclip']

	@property
	def isAutoSwap(self) -> bool:
		"""Property indicating whether to automatically swap languages ​​when there is no entry in the dictionary.
		@return: value stored in the add-on configuration
		@rtype: bool
		"""
		return config.conf[_addonName]['autoswap']

	@property
	def isSwitchSynth(self) -> bool:
		"""Property indicate whether to switch the synthesizer when sounding the dictionary entry.
		@return: value stored in the add-on configuration
		@rtype: bool
		"""
		return config.conf[_addonName]['switchsynth']

	def terminate(self, *args, **kwargs):
		"""This will be called when NVDA is finished with this global plugin"""
		super().terminate(*args, **kwargs)
		try:
			gui.settingsDialogs.NVDASettingsDialog.categoryClasses.remove(QuickDictionarySettingsPanel)
		except IndexError:
			log.warning("Can't remove %s Settings panel from NVDA settings dialogs", _addonSummary)

	def getScript(self, gesture):
		"""Retrieve the script bound to a given gesture.
		@param gesture: the input gesture in question
		@type gesture: L{inputCore.InputGesture}
		@return: the necessary method or method that handles the error
		@rtype: script function
		"""
		if not self._toggleGestures:
			return globalPluginHandler.GlobalPlugin.getScript(self, gesture)
		script = globalPluginHandler.GlobalPlugin.getScript(self, gesture)
		if not script:
			script = finally_(self.script_error, self.finish)
		return finally_(script, self.finish)

	def finish(self):
		"""Switching back to original gestures"""
		self._toggleGestures = False
		self.clearGestureBindings()
		self.bindGestures(self.__gestures)

	@script(description='')
	def script_error(self, gesture):
		"""Called when the wrong gestures are using in add-on control mode.
		@param gesture: the input gesture in question
		@type gesture: L{inputCore.InputGesture}
		"""
		beep(100, 100)

	# Translators: Method description is displayed in the NVDA input gestures dialog
	@script(description="%s, %s" % (_addonSummary, _("then press %s for help") % 'H'))
	def script_addonLayer(self, gesture):
		"""A run-time binding will occur from which we can perform various layered dictionary commands.
		First, check if a second press of the script was done.
		@param gesture: gesture assigned to this method
		@type gesture: L{inputCore.InputGesture}
		"""
		if self._toggleGestures:
			self.script_error(gesture)
			return
		self.bindGestures(self.__addonGestures)
		self._toggleGestures = True
		beep(200, 10)

	# Translators: Method description included in the add-on help message and NVDA input gestures dialog
	@script(description="D - %s" % _("announce the dictionary entry for the currently selected word or phrase (the same as %s)") % 'NVDA+Y')
	def script_dictionaryAnnounce(self, gesture):
		"""Receive and read a dictionary entry for the selected text or text from the clipboard.
		@param gesture: gesture assigned to this method
		@type gesture: L{inputCore.InputGesture}
		"""
		text = getSelectedText()
		if not text: return
		Thread(target=self.translate, args=[text, False]).start()

	# Translators: Method description included in the add-on help message and NVDA input gestures dialog
	@script(description="W - %s" % _("show dictionary entry in a separate browseable window"))
	def script_dictionaryBox(self, gesture):
		"""Receive and show in browseable window dictionary entry
		for the selected word/phrase or text from the clipboard.
		@param gesture: gesture assigned to this method
		@type gesture: L{inputCore.InputGesture}
		"""
		text = getSelectedText()
		if not text: return
		Thread(target=self.translate, args=[text, True]).start()

	# Translators: Method description included in the add-on help message and NVDA input gestures dialog
	@script(description="A - %s" % _("announce the current source and target languages"))
	def script_announceLanguages(self, gesture):
		"""Pronounce the current pair of selected languages.
		@param gesture: gesture assigned to this method
		@type gesture: L{inputCore.InputGesture}
		"""
		# Translators: message presented to announce the current source and target languages.
		ui.message(_("Translate: from {langFrom} to {langInto}").format(langFrom=langs[self.source].name, langInto=langs[self.target].name))

	# Translators: Method description included in the add-on help message and NVDA input gestures dialog
	@script(description="S - %s" % _("swap languages and get Quick Dictionary translation"))
	def script_swapLanguages(self, gesture):
		"""Swap languages ​​and present the dictionary entry for the selected word or phrase.
		@param gesture: gesture assigned to this method
		@type gesture: L{inputCore.InputGesture}
		"""
		if langs.isAvailable(self.target, self.source):
			self.source, self.target = self.target, self.source
			# Translators: Notification that languages ​​have been swapped
			ui.message(_("Languages swapped"))
			ui.message('%s - %s' % (self.source, self.target))
			text = getSelectedText()
			if not text: return
			Thread(target=self.translate, args=[text, False]).start()
		else:
			# Translators: Notification that reverse translation is not available for the current language pair
			ui.message(_("Swap languages is not available for this pair") + ": %s - %s" % (langs[self.source].name, langs[self.target].name))

	# Translators: Method description included in the add-on help message and NVDA input gestures dialog
	@script(description="C - %s" % _("copy last dictionary entry to the clipboard"))
	def script_copyLastResult(self, gesture):
		"""Copy the last received dictionary entry to the clipboard.
		@param gesture: gesture assigned to this method
		@type gesture: L{inputCore.InputGesture}
		"""
		if not self._lastTranslator:
			# Translators: Notification that no dictionary entries have been received in the current session
			ui.message(_("There is no dictionary queries"))
			return
		copyToClipboard(self._lastTranslator.plaintext)
		ui.message('%s - %s' % (langs[self._lastTranslator.langFrom].name, langs[self._lastTranslator.langTo].name))
		ui.message(self._lastTranslator.plaintext)

	# Translators: Method description included in the add-on help message and NVDA input gestures dialog
	@script(description="H - %s" % _("announce the add-on help message"))
	def script_announceHelp(self, gesture):
		"""Retrieves a description of all add-ons methods and presents them.
		@param gesture: gesture assigned to this method
		@type gesture: L{inputCore.InputGesture}
		"""
		for message in [
			_addonSummary,
			# Translators: Message in the add-on short help
			"NVDA+Y - %s" % _("switch to add-on control mode"),
			# Translators: Message in the add-on short help
			_("to get a quick translation of a word or phrase - press %s twice") % "NVDA+Y",
			"...",
			# Translators: Message in the add-on short help
			_("In add-on gestures layer mode:"),
			self.script_dictionaryAnnounce.__doc__,
			self.script_dictionaryBox.__doc__,
			self.script_swapLanguages.__doc__,
			self.script_announceLanguages.__doc__,
			self.script_copyLastResult.__doc__,
			"...",
			# Translators: Message in the add-on short help
			_("Voice synthesizers profiles management:"),
			self.script_selectSynthProfile.__doc__,
			self.script_announceSelectedSynthProfile.__doc__,
			self.script_announceSynthProfiles.__doc__,
			self.script_restoreDefaultSynth.__doc__,
			self.script_removeSynthProfile.__doc__,
			self.script_saveSynthProfile.__doc__,
			"...",
			self.script_showSettings.__doc__,
			self.script_announceHelp.__doc__,
			# Translators: Message in the add-on short help
			_("for any of the listed features you can customize the keyboard shortcut in NVDA input gestures dialog")]:
			ui.message(message)

	# Translators: Method description included in the add-on help message and NVDA input gestures dialog
	@script(description="O - %s" % _("open add-on settings dialog"))
	def script_showSettings(self, gesture):
		"""Display the add-on settings dialog.
		@param gesture: gesture assigned to this method
		@type gesture: L{inputCore.InputGesture}
		"""
		wx.CallAfter(gui.mainFrame._popupSettingsDialog, gui.settingsDialogs.NVDASettingsDialog, QuickDictionarySettingsPanel)

	# Translators: Method description included in the add-on help message and NVDA input gestures dialog
	@script(description=_("From %d to %d - selection of the voice synthesizer profile") % (1, 9))
	def script_selectSynthProfile(self, gesture):
		"""Switch between voice synthesizer profiles.
		@param gesture: gesture assigned to this method
		@type gesture: L{inputCore.InputGesture}
		"""
		self._slot = int(gesture.displayName[-1])
		profiles[self._slot].set()
		# Translators: Message when selecting a voice synthesizer profile
		ui.message(_("Profile %d selected: %s") % (self._slot, profiles[self._slot].title))

	# Translators: Method description included in the add-on help message and NVDA input gestures dialog
	@script(description="G - %s" % _("announce the selected profile of voice synthesizers"))
	def script_announceSelectedSynthProfile(self, gesture):
		"""Announce the number and title of the currently selected voice synthesizer profile.
		@param gesture: gesture assigned to this method
		@type gesture: L{inputCore.InputGesture}
		"""
		ui.message("%d - %s" % (self._slot, profiles[self._slot].title))

	# Translators: Method description is displayed in the NVDA gestures dialog
	@script(description="P - %s" % _("announce a list of all customized voice synthesizers profiles"))
	def script_announceSynthProfiles(self, gesture):
		"""Announce a list of of all configured voice synthesizers profiles and the associated languages.
		@param gesture: gesture assigned to this method
		@type gesture: L{inputCore.InputGesture}
		"""
		for slot, profile in profiles:
			if profile.name:
				ui.message("%d: %s" % (slot, ', '.join([profile.title, langs[profile.lang].name])))

	# Translators: Method description is displayed in the NVDA gestures dialog
	@script(description="Del - %s" % _("delete the selected voice synthesizer profile"))
	def script_removeSynthProfile(self, gesture):
		"""Delete the currently selected voice synthesizer profile.
		@param gesture: gesture assigned to this method
		@type gesture: L{inputCore.InputGesture}
		"""
		slot, self._slot = self._slot, 1
		profiles.remove(slot)
		# Translators: 
		ui.message(_("Profile %d successfully deleted") % slot)

	# Translators: Method description is displayed in the NVDA gestures dialog
	@script(description="R - %s" % _("restore default voice synthesizer"))
	def script_restoreDefaultSynth(self, gesture):
		"""Restore default voice synthesizer from previously saved profile.
		@param gesture: gesture assigned to this method
		@type gesture: L{inputCore.InputGesture}
		"""
		profile = profiles.restoreDefault()
		ui.message(profile.title)

	# Translators: Method description is displayed in the NVDA gestures dialog
	@script(description="V - %s" % _("save configured voice synthesizer profile"))
	def script_saveSynthProfile(self, gesture):
		"""Save configured voice synthesizer profile.
		@param gesture: gesture assigned to this method
		@type gesture: L{inputCore.InputGesture}
		"""
		profiles[self._slot].update()
		profiles.save()
		# Translators: Announcing after saving synthesizer profile
		ui.message(_("Voice synthesizer profile saved successfully"))

	def translate(self, text:str, isHtml:bool=False):
		"""Retrieve the dictionary entry for the given word or phrase and display/announce the result.
		This method must always be called in a separate thread so as not to block NVDA.
		@param text: a word or phrase to look up in a dictionary
		@type text: str
		@param isHtml: a sign of whether it is necessary to display the result of work in the form of HTML page
		@type isHtml: bool
		@return: None
		"""
		pairs = [(self.source, self.target)]
		if self.isAutoSwap:
			pairs.append((self.target, self.source))
		for lFrom, lInto in pairs:
			translator = translateWithCaching(lFrom, lInto, text)
			if translator.plaintext:
				break
		else:
			if not translator.plaintext:
				# Translators: Notification of missing dictionary entry for current request
				ui.message(_("No results"))
				return
		self._lastTranslator = translator
		if isHtml:
			ui.browseableMessage(translator.html, title='%s-%s' % (langs[translator.langFrom].name, langs[translator.langTo].name), isHtml=isHtml)
		else:
			ui.message('%s - %s' % (langs[translator.langFrom].name, langs[translator.langTo].name))
			queueFunction(eventQueue, messageWithLangDetection,
				{'text': translator.plaintext, 'lang': translator.langTo})
		if self.isCopyToClipboard:
			copyToClipboard(translator.plaintext)

	__addonGestures = {
		"kb:NVDA+y": "dictionaryAnnounce",
		"kb:d": "dictionaryAnnounce",
		"kb:w": "dictionaryBox",
		"kb:a": "announceLanguages",
		"kb:s": "swapLanguages",
		"kb:c": "copyLastResult",
		"kb:o": "showSettings",
		"kb:h": "announceHelp",
		"kb:g": "announceSelectedSynthProfile",
		"kb:p": "announceSynthProfiles",
		"kb:delete": "removeSynthProfile",
		"kb:r": "restoreDefaultSynth",
		"kb:v": "saveSynthProfile",
		"kb:1": "selectSynthProfile",
		"kb:2": "selectSynthProfile",
		"kb:3": "selectSynthProfile",
		"kb:4": "selectSynthProfile",
		"kb:5": "selectSynthProfile",
		"kb:6": "selectSynthProfile",
		"kb:7": "selectSynthProfile",
		"kb:8": "selectSynthProfile",
		"kb:9": "selectSynthProfile",
	}

	__gestures = {
		"kb:NVDA+y": "addonLayer",
	}
