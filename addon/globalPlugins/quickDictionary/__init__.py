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
from time import sleep
from threading import Thread
from .locator import services
from .shared import copyToClipboard, getSelectedText, translateWithCaching, messageWithLangDetection, finally_
from .synthesizers import profiles
from .template import htmlTemplate


class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	"""Implementation global commands of NVDA add-on"""
	scriptCategory = _addonSummary

	def __init__(self, *args, **kwargs):
		"""Initializing initial configuration values ​​and other fields"""
		super(GlobalPlugin, self).__init__(*args, **kwargs)
		confspec = {
			"active": "integer(default=0,min=0,max=9)",
			"switchsynth": "boolean(default=true)"
		}
		config.conf.spec[_addonName] = confspec
		for service in services:
			config.conf.spec[_addonName][service.name] = service.confspec
		global langs
		langs = services[config.conf[_addonName]['active']].langs
		gui.settingsDialogs.NVDASettingsDialog.categoryClasses.append(services[config.conf[_addonName]['active']].settings)
		# to use the second layer of keyboard shortcuts
		self._toggleGestures = False
		# to use copy latest translation to the clipboard
		self._lastTranslator = None
		# to use speech synthesizers profiles
		self._slot = 1
		# to switch between services
		self._gate = config.conf[_addonName]['active']+1
		# Sequence of messages
		self._messages = []

	@property
	def source(self) -> str:
		"""Source language for translation.
		@return: usually two-character language code
		@rtype: str
		"""
		return config.conf[_addonName][services[config.conf[_addonName]['active']].name]['from']

	@source.setter
	def source(self, lang: str):
		"""Setter for source language.
		@param lang: usually two-character language code
		@type lang: str
		"""
		config.conf[_addonName][services[config.conf[_addonName]['active']].name]['from'] = lang

	@property
	def target(self) -> str:
		"""Target language for translation.
		@return: usually two-character language code
		@rtype: str
		"""
		return config.conf[_addonName][services[config.conf[_addonName]['active']].name]['into']

	@target.setter
	def target(self, lang: str):
		"""Setter for target language.
		@param lang: usually two-character language code
		@type lang: str
		"""
		config.conf[_addonName][services[config.conf[_addonName]['active']].name]['into'] = lang

	@property
	def isCopyToClipboard(self) -> bool:
		"""Property specifying whether to copy the dictionary results to the clipboard each time.
		@return: value stored in the add-on configuration
		@rtype: bool
		"""
		return config.conf[_addonName][services[config.conf[_addonName]['active']].name]['copytoclip']

	@property
	def isAutoSwap(self) -> bool:
		"""Property indicating whether to automatically swap languages ​​when there is no entry in the dictionary.
		@return: value stored in the add-on configuration
		@rtype: bool
		"""
		return config.conf[_addonName][services[config.conf[_addonName]['active']].name]['autoswap']

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
			gui.settingsDialogs.NVDASettingsDialog.categoryClasses.remove(services[config.conf[_addonName]['active']].settings)
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
			self._messages.append(_("Languages swapped"))
			self._messages.append('%s - %s' % (self.source, self.target))
			text = getSelectedText()
			if not text:
				ui.message('...'.join(self._messages))
				self._messages.clear()
				return
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
	@script(description="U - %s" % _("download from online dictionary and save the current list of available languages"))
	def script_updateLanguages(self, gesture):
		"""Download a list of available languages from the online dictionary and save them to a local file.
		@param gesture: gesture assigned to this method
		@type gesture: L{inputCore.InputGesture}
		"""
		Thread(target=self.downloadLanguages).start()

	def downloadLanguages(self):
		"""Download current list of available languages from the remote server and save them to a local file.
		Call the request procedure to the remote server on a separate thread.
		Wait for the request to complete and return a prepared response.
		"""
		load = Thread(target=langs.update)
		load.start()
		i=0
		while load.is_alive():
			sleep(0.1)
			if i == 10:
				beep(500, 100)
				i = 0
			i+=1
		load.join()
		if langs.updated:
			# Translators: Notification when downloading from the online dictionary list of available languages
			ui.message(_("The list of available languages ​​has been successfully downloaded and saved."))
			langs.updated = False
		else:
			# Translators: Notification when downloading from the online dictionary list of available languages
			ui.message(_("Warning! The list of available languages could not be loaded."))

	# Translators: Method description included in the add-on help message and NVDA input gestures dialog
	@script(description="H - %s" % _("add-on help page"))
	def script_help(self, gesture):
		"""Retrieves a description of all add-ons methods and presents them.
		@param gesture: gesture assigned to this method
		@type gesture: L{inputCore.InputGesture}
		"""
		lines = [
			"<h1>%s</h1>" % _addonSummary,
			# Translators: Message in the add-on short help
			"<p>NVDA+Y - %s,</p>" % _("switch to add-on control mode"),
			# Translators: Message in the add-on short help
			"<p>%s.</p>" % _("to get a quick translation of a word or phrase - press %s twice") % "NVDA+Y",
			"<br>",
			# Translators: Message in the add-on short help
			"<h2>%s</h2>" % _("In add-on gestures layer mode:"),
			'<ul type="disc">']
		for method in [
			self.script_dictionaryAnnounce.__doc__,
			self.script_dictionaryBox.__doc__,
			self.script_swapLanguages.__doc__,
			self.script_announceLanguages.__doc__,
			self.script_copyLastResult.__doc__,
			self.script_updateLanguages.__doc__,
			self.script_selectService.__doc__]:
			lines.append("<li>%s</li>" % method)
		lines += ["</ul>", "<br>",
			# Translators: Message in the add-on short help
			"<h2>%s</h2>" % _("Voice synthesizers profiles management:"),
			'<ul type="disc">']
		for method in [
			self.script_selectSynthProfile.__doc__,
			self.script_announceSelectedSynthProfile.__doc__,
			self.script_announceAllSynthProfiles.__doc__,
			self.script_restorePreviousSynth.__doc__,
			self.script_restoreDefaultSynth.__doc__,
			self.script_removeSynthProfile.__doc__,
			self.script_saveSynthProfile.__doc__]:
			lines.append("<li>%s</li>" % method)
		lines += ["</ul>", "<br>"]
		for line in [
			self.script_showSettings.__doc__,
			self.script_help.__doc__,
			# Translators: Message in the add-on short help
			_("for any of the listed features you can customize the keyboard shortcut in NVDA input gestures dialog")]:
			lines.append("<p>%s.</p>" % line.capitalize())
		ui.browseableMessage(htmlTemplate.format(body=''.join(lines)),
			_("add-on help page").capitalize(), True)

	# Translators: Method description included in the add-on help message and NVDA input gestures dialog
	@script(description="O - %s" % _("open add-on settings dialog"))
	def script_showSettings(self, gesture):
		"""Display the add-on settings dialog.
		@param gesture: gesture assigned to this method
		@type gesture: L{inputCore.InputGesture}
		"""
		wx.CallAfter(gui.mainFrame._popupSettingsDialog, gui.settingsDialogs.NVDASettingsDialog, services[config.conf[_addonName]['active']].settings)

	# Translators: Method description included in the add-on help message and NVDA input gestures dialog
	@script(description=_("From {startslot} to {endslot} - selection of the voice synthesizer profile").format(startslot=1, endslot=9))
	def script_selectSynthProfile(self, gesture):
		"""Switch between voice synthesizer profiles.
		@param gesture: gesture assigned to this method
		@type gesture: L{inputCore.InputGesture}
		"""
		self._slot = int(gesture.displayName[-1])
		profiles.rememberCurrent()
		profiles[self._slot].set()
		# Translators: Message when selecting a voice synthesizer profile
		ui.message(_("Profile {slot} selected: {title}").format(slot=self._slot, title=profiles[self._slot].title))

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
	def script_announceAllSynthProfiles(self, gesture):
		"""Announce a list of of all configured voice synthesizers profiles and the associated languages.
		@param gesture: gesture assigned to this method
		@type gesture: L{inputCore.InputGesture}
		"""
		if len(profiles)==0:
			# Translators: Notification of no configured profiles
			ui.message(_("Please set up voice synthesizers profiles."))
			return
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
		profiles.restorePrevious()
		# Translators: Message when deleting a profile
		ui.message(_("Profile %d successfully deleted") % slot)

	# Translators: Method description is displayed in the NVDA gestures dialog
	@script(description="R - %s" % _("restore default voice synthesizer"))
	def script_restoreDefaultSynth(self, gesture):
		"""Restore default voice synthesizer from previously saved profile.
		@param gesture: gesture assigned to this method
		@type gesture: L{inputCore.InputGesture}
		"""
		profiles.rememberCurrent()
		profile = profiles.restoreDefault()
		ui.message(profile.title)

	# Translators: Method description is displayed in the NVDA gestures dialog
	@script(description="B - %s" % _("back to previous voice synthesizer"))
	def script_restorePreviousSynth(self, gesture):
		"""Restore previous voice synthesizer if profile was saved before switching.
		@param gesture: gesture assigned to this method
		@type gesture: L{inputCore.InputGesture}
		"""
		current = profiles.getCurrent()
		profile = profiles.restorePrevious()
		profiles.rememberCurrent(current)
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

	# Translators: Method description included in the add-on help message and NVDA input gestures dialog
	@script(description=_("From F1 to F{endgate} - select online dictionary service").format(endgate=len(services)))
	def script_selectService(self, gesture):
		"""
		@param gesture: gesture assigned to this method
		@type gesture: L{inputCore.InputGesture}
		"""
		self._gate = min(int(gesture.displayName[-1]), len(services))
		config.conf[_addonName]['active'] = self._gate - 1
		ui.message(': '.join([gesture.displayName, services[self._gate-1].summary]))

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
			if langs.isAvailable(self.target, self.source):
				pairs.append((self.target, self.source))
		for lFrom, lInto in pairs:
			translator = translateWithCaching(lFrom, lInto, text)
			if translator.plaintext:
				break
		else:
			if not translator.plaintext:
				# Translators: Notification of missing dictionary entry for current request
				ui.message(_("No results"))
				self._messages.clear()
				return
		self._lastTranslator = translator
		if isHtml:
			ui.browseableMessage(translator.html, title='%s-%s' % (langs[translator.langFrom].name, langs[translator.langTo].name), isHtml=isHtml)
		else:
			if config.conf[_addonName]['switchsynth']:
				profile = next(filter(lambda x: x.lang==translator.langTo, (p for s,p in profiles)), None)
				if profile:
					profile.set()
			self._messages.append('%s - %s' % (langs[translator.langFrom].name, langs[translator.langTo].name))
			self._messages.append(translator.plaintext)
			message = '...'.join(self._messages)
			self._messages.clear()
			queueFunction(eventQueue, messageWithLangDetection,
				{'text': message, 'lang': translator.langTo})
		if self.isCopyToClipboard:
			copyToClipboard(translator.plaintext)

	__addonGestures = {
		# Dictionary
		"kb:NVDA+y": "dictionaryAnnounce",
		"kb:d": "dictionaryAnnounce",
		"kb:w": "dictionaryBox",
		"kb:a": "announceLanguages",
		"kb:s": "swapLanguages",
		"kb:c": "copyLastResult",
		"kb:u": "updateLanguages",
		# General
		"kb:o": "showSettings",
		"kb:h": "help",
		# Profiles of voice synthesizers
		"kb:g": "announceSelectedSynthProfile",
		"kb:p": "announceAllSynthProfiles",
		"kb:delete": "removeSynthProfile",
		"kb:b": "restorePreviousSynth",
		"kb:r": "restoreDefaultSynth",
		"kb:v": "saveSynthProfile",
	}
	for key in range(1, 10):
		__addonGestures["kb:%d" % key] = "selectSynthProfile"
	for key in range(1, len(services)+1):
		__addonGestures["kb:f%d" % key] = "selectService"

	__gestures = {
		"kb:NVDA+y": "addonLayer",
	}
