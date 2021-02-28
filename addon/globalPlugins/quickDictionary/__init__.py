#-*- coding:utf-8 -*-
# A part of the NVDA Quick Dictionary add-on
# This file is covered by the GNU General Public License.
# See the file COPYING for more details.
# Copyright (C) 2020-2021 Olexandr Gryshchenko <grisov.nvaccess@mailnull.com>

from typing import Optional, Callable, Dict, List
import addonHandler
from logHandler import log
try:
	addonHandler.initTranslation()
except addonHandler.AddonError:
	log.warning("Unable to initialise translations. This may be because the addon is running from NVDA scratchpad.")
_: Callable[[str], str]

import os
_addonDir = os.path.join(os.path.dirname(__file__), "..", "..")
if isinstance(_addonDir, bytes):
	_addonDir = _addonDir.decode("mbcs")
_curAddon = addonHandler.Addon(_addonDir)
_addonName: str = _curAddon.manifest['name']
_addonSummary: str = _curAddon.manifest['summary']

import globalPluginHandler
from globalVars import appArgs
from scriptHandler import script
from queueHandler import queueFunction, eventQueue
import api, ui, config
import gui, wx
from tones import beep
from inputCore import InputGesture
from time import sleep
from threading import Thread
from .locator import services
from .shared import getSelectedText, translateWithCaching, hashForCache, waitingFor, messageWithLangDetection, finally_, htmlTemplate
from .synthesizers import profiles
from .settings import QDSettingsPanel, SynthesizersDialog, ServicesDialog, EditableInputDialog
from .service import Translator


class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	"""Implementation global commands of NVDA add-on"""
	scriptCategory: str = _addonSummary

	def __init__(self, *args, **kwargs) -> None:
		"""Initializing initial configuration values ​​and other fields"""
		super(GlobalPlugin, self).__init__(*args, **kwargs)
		if appArgs.secure or config.isAppX:
			return
		confspec = {
			"active": "integer(default=0,min=0,max=9)",
		}
		config.conf.spec[_addonName] = confspec
		for service in services:
			config.conf.spec[_addonName][service.name] = service.confspec
		gui.settingsDialogs.NVDASettingsDialog.categoryClasses.append(QDSettingsPanel)
		# to use the second layer of keyboard shortcuts
		self._toggleGestures: bool = False
		# to use copy latest translation to the clipboard
		self._lastTranslator: Optional[Translator] = None
		# to use speech synthesizers profiles
		self._slot: int = 1
		# to switch between services
		self._gate: int = config.conf[_addonName]['active']+1
		# storing information about the state of the cache
		self._cacheInfo: str = ''
		# Sequence of messages
		self._messages: List[str] = []
		self.createSubMenu()

	def createSubMenu(self) -> None:
		"""Build a submenu in the "tools" menu."""
		self.menu = gui.mainFrame.sysTrayIcon.toolsMenu
		subMenu = wx.Menu()
		self.mainItem = self.menu.AppendSubMenu(subMenu, _addonSummary)
		# Translators: the name of a submenu item (also used as method description).
		preEditItem = subMenu.Append(wx.ID_ANY, _("edit text before sending").capitalize() + '...')
		gui.mainFrame.sysTrayIcon.Bind(wx.EVT_MENU, lambda event: self.preEditDialog(), preEditItem)
		# Translators: the name of a submenu item (also used as method description).
		chooseServiceItem = subMenu.Append(wx.ID_ANY, _("choose online service").capitalize() + '...')
		gui.mainFrame.sysTrayIcon.Bind(wx.EVT_MENU, lambda event: self.chooseServiceDialog(), chooseServiceItem)
		# Translators: the name of a submenu item (also used as dialog title).
		synthsProfilesItem = subMenu.Append(wx.ID_ANY, _("Voice synthesizers profiles") + '...')
		gui.mainFrame.sysTrayIcon.Bind(wx.EVT_MENU, lambda event: self.synthsProfilesDialog(), synthsProfilesItem)
		# Translators: the name of a submenu item
		settingsItem = subMenu.Append(wx.ID_ANY, _("&Options..."))
		gui.mainFrame.sysTrayIcon.Bind(wx.EVT_MENU, lambda event: self.addonSettingsDialog(), settingsItem)
		# Translators: the name of a submenu item (also used as dialog title).
		cmdHelpItem = subMenu.Append(wx.ID_ANY, _("help on add-on commands").capitalize())
		gui.mainFrame.sysTrayIcon.Bind(wx.EVT_MENU, lambda event: self.addonHelpPage(), cmdHelpItem)
		helpFile = _curAddon.getDocFilePath().replace("readme.html", "index.html")
		# If there is no localized file - open the English version
		if not os.path.isfile(helpFile):
			locale = helpFile.split('\\')[-2]
			helpFile = _curAddon.getDocFilePath().replace("\\%s\\readme.html" % locale, "\\en\\index.html")
		if os.path.isfile(helpFile):
			# Translators: the name of a submenu item
			helpItem = subMenu.Append(wx.ID_ANY, _("He&lp"))
			gui.mainFrame.sysTrayIcon.Bind(wx.EVT_MENU, lambda event: self.openHelp(helpFile), helpItem)

	def openHelp(self, helpFile: str) -> None:
		"""Open the add-on help page in the default browser.
		@param helpFile: HTML-file with complete help information on the add-on
		@type helpFile: str
		"""
		import webbrowser
		webbrowser.open(helpFile)

	@property
	def source(self) -> str:
		"""Source language for translation.
		@return: usually two-character language code
		@rtype: str
		"""
		return config.conf[_addonName][services[config.conf[_addonName]['active']].name]['from']

	@source.setter
	def source(self, lang: str) -> None:
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
	def target(self, lang: str) -> None:
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

	def terminate(self, *args, **kwargs) -> None:
		"""This will be called when NVDA is finished with this global plugin."""
		super().terminate(*args, **kwargs)
		try:
			gui.settingsDialogs.NVDASettingsDialog.categoryClasses.remove(QDSettingsPanel)
		except IndexError:
			log.warning("Can't remove %s Settings panel from NVDA settings dialogs", _addonSummary)
		try:
			self.menu.Remove(self.mainItem)
		except (RuntimeError, AttributeError):
			log.warning("Can't remove %s submenu from NVDA menu", _addonSummary)

	def getScript(self, gesture: InputGesture) -> Callable:
		"""Retrieve the script bound to a given gesture.
		@param gesture: the input gesture in question
		@type gesture: InputGesture
		@return: the necessary method or method that handles the error
		@rtype: Callable
		"""
		if not self._toggleGestures:
			return globalPluginHandler.GlobalPlugin.getScript(self, gesture)
		script = globalPluginHandler.GlobalPlugin.getScript(self, gesture)
		if not script:
			script = finally_(self.script_error, self.finish)
		return finally_(script, self.finish)

	def finish(self) -> None:
		"""Switching back to original gestures."""
		self._toggleGestures = False
		self.clearGestureBindings()
		self.bindGestures(self.__gestures)

	@script(description=None)
	def script_error(self, gesture: InputGesture) -> None:
		"""Call when the wrong gestures are using in add-on control mode.
		@param gesture: the input gesture in question
		@type gesture: InputGesture
		"""
		beep(100, 100)

	# Translators: Method description is displayed in the NVDA input gestures dialog
	@script(description="%s, %s" % (_addonSummary, _("then press %s for help") % 'H'))
	def script_addonLayer(self, gesture: InputGesture) -> None:
		"""A run-time binding will occur from which we can perform various layered dictionary commands.
		First, check if a second press of the script was done.
		@param gesture: gesture assigned to this method
		@type gesture: InputGesture
		"""
		if self._toggleGestures:
			self.script_error(gesture)
			return
		self.bindGestures(self.__addonGestures)
		self._toggleGestures = True
		beep(200, 10)

	# Translators: Method description included in the add-on help message and NVDA input gestures dialog
	@script(description="D - %s" % _("announce the dictionary entry for the currently selected word or phrase (the same as %s)") % 'NVDA+Y')
	def script_dictionaryAnnounce(self, gesture: InputGesture) -> None:
		"""Receive and read a dictionary entry for the selected text or text from the clipboard.
		@param gesture: gesture assigned to this method
		@type gesture: InputGesture
		"""
		text = getSelectedText()
		if not text: return
		Thread(target=self.translate, args=[text, False]).start()

	# Translators: Method description included in the add-on help message and NVDA input gestures dialog
	@script(description="W - %s" % _("show dictionary entry in a separate browseable window"))
	def script_dictionaryBox(self, gesture: InputGesture) -> None:
		"""Receive and show in browseable window dictionary entry
		for the selected word/phrase or text from the clipboard.
		@param gesture: gesture assigned to this method
		@type gesture: InputGesture
		"""
		text = getSelectedText()
		if not text: return
		Thread(target=self.translate, args=[text, True]).start()

	# Translators: Method description included in the add-on help message and NVDA input gestures dialog
	@script(description="E - %s" % _("edit text before sending"))
	def script_editText(self, gesture: InputGesture) -> None:
		"""Dialog to edit the selected word/phrase or text from the clipboard before sending it to the translation.
		@param gesture: gesture assigned to this method
		@type gesture: InputGesture
		"""
		self.preEditDialog()

	def preEditDialog(self) -> None:
		"""Dialog for pre-editing text before sending it for translation."""
		def resultHandler(result: int, dlg: wx.Dialog) -> None:
			"""Processing data obtained from the dialog."""
			if result==wx.ID_OK:
				if not dlg.text: return
				Thread(target=self.translate, args=[dlg.text, True]).start()
		text = getSelectedText()
		# Translators: The title of the dialog to edit the text before sending it for translation
		ed = EditableInputDialog(parent=gui.mainFrame, id=wx.ID_ANY, title=_("edit text before sending").capitalize(), text=text)
		gui.runScriptModalDialog(ed, callback=lambda result: resultHandler(result, ed))

	# Translators: Method description included in the add-on help message and NVDA input gestures dialog
	@script(description="A - %s" % _("announce the current source and target languages"))
	def script_announceLanguages(self, gesture: InputGesture) -> None:
		"""Pronounce the current pair of selected languages.
		@param gesture: gesture assigned to this method
		@type gesture: InputGesture
		"""
		langs = services[config.conf[_addonName]['active']].langs
		# Translators: message presented to announce the current source and target languages.
		ui.message(_("Translate: from {langFrom} to {langInto}").format(langFrom=langs[self.source].name, langInto=langs[self.target].name))

	# Translators: Method description included in the add-on help message and NVDA input gestures dialog
	@script(description="S - %s" % _("swap languages and get Quick Dictionary translation"))
	def script_swapLanguages(self, gesture: InputGesture) -> None:
		"""Swap languages ​​and present the dictionary entry for the selected word or phrase.
		@param gesture: gesture assigned to this method
		@type gesture: InputGesture
		"""
		langs = services[config.conf[_addonName]['active']].langs
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
	def script_copyLastResult(self, gesture: InputGesture) -> None:
		"""Copy the last received dictionary entry to the clipboard.
		@param gesture: gesture assigned to this method
		@type gesture: InputGesture
		"""
		if not self._lastTranslator:
			# Translators: Notification that no dictionary entries have been received in the current session
			ui.message(_("There is no dictionary queries"))
			return
		langs = services[config.conf[_addonName]['active']].langs
		api.copyToClip(self._lastTranslator.plaintext, notify=True)
		ui.message('%s - %s' % (langs[self._lastTranslator.langFrom].name, langs[self._lastTranslator.langTo].name))

	# Translators: Method description included in the add-on help message and NVDA input gestures dialog
	@script(description="U - %s" % _("download from online dictionary and save the current list of available languages"))
	def script_updateLanguages(self, gesture: InputGesture) -> None:
		"""Download a list of available languages from the online dictionary and save them to a local file.
		@param gesture: gesture assigned to this method
		@type gesture: InputGesture
		"""
		def downloadLanguages() -> None:
			"""Download current list of available languages from the remote server and save them to a local file.
			Wait for the request to complete and return a prepared response.
			"""
			langs = services[config.conf[_addonName]['active']].langs
			waitingFor(langs.update)
			if langs.updated:
				# Translators: Notification when downloading from the online dictionary list of available languages
				ui.message(_("The list of available languages ​​has been successfully downloaded and saved."))
			else:
				# Translators: Notification when downloading from the online dictionary list of available languages
				ui.message(_("Warning! The list of available languages could not be loaded."))
		Thread(target=downloadLanguages).start()

	# Translators: Method description included in the add-on help message and NVDA input gestures dialog
	@script(description="Q - %s" % _("statistics on the using the online service"))
	def script_dictionaryStatistics(self, gesture: InputGesture) -> None:
		"""Available statistical information on the use of the current online service.
		Service summary, the number of executed requests in the current session, the balance of the daily quota,
		time remaining until the daily quota is updated, cache status information.
		@param gesture: gesture assigned to this method
		@type gesture: InputGesture
		"""
		service = services[config.conf[_addonName]['active']]
		ui.message(service.summary)
		# Translators: Information about the online service
		ui.message(_("supports {number} languages").format(number=len(service.langs.all)))
		if config.conf[_addonName][service.name].get('source'):
			# Translators: The name of the field displayed in the statistics and in the settings panel
			ui.message("{title} - {source}".format(title=_("&Dictionary:").replace('&', ''), source=config.conf[_addonName][service.name]['source']))
		if not service.stat:
			# Translators: Information about the online service
			ui.message(_("There is no dictionary queries"))
		if service.stat.get('count'):
			# Translators: Information about the online service
			ui.message(_("performed {count} requests").format(count=service.stat['count']))
		if service.stat.get('remain'):
			# Translators: Information about the online service
			ui.message(_("available {remain}").format(remain=service.stat['remain']))
		from datetime import datetime, timedelta
		if isinstance(service.stat.get('delta'), timedelta):
			tomorrow = datetime.now() + timedelta(days=1)
			middle = datetime(tomorrow.year, tomorrow.month, tomorrow.day)
			hours, seconds = divmod((middle + service.stat['delta'] - datetime.now()).seconds, 3600)
			minutes, seconds = divmod(seconds, 60)
			# Translators: Information about the online service
			ui.message(_("the limit will be reset in {hours} hours {minutes} minutes").format(
				hours=hours, minutes=minutes))
		if self._cacheInfo:
			# Translators: Information about the cache state
			ui.message("%s: %s" % (_("state of cache"), self._cacheInfo))

	# Translators: Method description included in the add-on help message and NVDA input gestures dialog
	@script(description="H - %s" % _("help on add-on commands"))
	def script_help(self, gesture: InputGesture) -> None:
		"""Retrieves a description of all add-ons methods and presents them.
		@param gesture: gesture assigned to this method
		@type gesture: InputGesture
		"""
		self.addonHelpPage()

	def addonHelpPage(self) -> None:
		"""Display the add-on help page.
		Call using keyboard commands or menu items.
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
			self.script_editText.__doc__,
			self.script_updateLanguages.__doc__,
			self.script_selectService.__doc__,
			self.script_dictionaryStatistics.__doc__]:
			lines.append("<li>%s</li>" % method)
		lines += ["</ul>", "<br>",
			# Translators: Message in the add-on short help
			"<h2>%s</h2>" % _("Voice synthesizers profiles management:"),
			'<ul type="disc">']
		for method in [
			self.script_selectSynthProfile.__doc__,
			self.script_announceSelectedSynthProfile.__doc__,
			self.script_restorePreviousSynth.__doc__,
			self.script_restoreDefaultSynth.__doc__,
			self.script_removeSynthProfile.__doc__,
			self.script_saveSynthProfile.__doc__,
			self.script_displayAllSynthProfiles.__doc__]:
			lines.append("<li>%s</li>" % method)
		lines += ["</ul>", "<br>"]
		for line in [
			self.script_servicesDialog.__doc__,
			self.script_showSettings.__doc__,
			self.script_help.__doc__,
			# Translators: Message in the add-on short help
			_("for any of the listed features you can customize the keyboard shortcut in NVDA input gestures dialog")]:
			lines.append("<p>%s.</p>" % line.capitalize())
		ui.browseableMessage(htmlTemplate.format(body=''.join(lines)),
			_("help on add-on commands").capitalize(), True)

	# Translators: Method description included in the add-on help message and NVDA input gestures dialog
	@script(description="O - %s" % _("open add-on settings dialog"))
	def script_showSettings(self, gesture: InputGesture) -> None:
		"""Display the add-on settings dialog.
		@param gesture: gesture assigned to this method
		@type gesture: InputGesture
		"""
		self.addonSettingsDialog()

	def addonSettingsDialog(self) -> None:
		"""Display the add-on settings dialog.
		Called using keyboard commands and menu items.
		"""
		wx.CallAfter(gui.mainFrame._popupSettingsDialog, gui.settingsDialogs.NVDASettingsDialog, QDSettingsPanel)

	# Translators: Method description included in the add-on help message and NVDA input gestures dialog
	@script(description=_("From {startslot} to {endslot} - selection of the voice synthesizer profile").format(startslot=1, endslot=9))
	def script_selectSynthProfile(self, gesture: InputGesture) -> None:
		"""Switch between voice synthesizer profiles.
		@param gesture: gesture assigned to this method
		@type gesture: InputGesture
		"""
		self._slot = int(gesture.mainKeyName[-1])
		profiles.rememberCurrent()
		profiles[self._slot].set()
		# Translators: Message when selecting a voice synthesizer profile
		ui.message(_("Profile {slot} selected: {title}").format(slot=self._slot, title=profiles[self._slot].title))

	# Translators: Method description included in the add-on help message and NVDA input gestures dialog
	@script(description="G - %s" % _("announce the selected profile of voice synthesizers"))
	def script_announceSelectedSynthProfile(self, gesture: InputGesture) -> None:
		"""Announce the number and title of the currently selected voice synthesizer profile.
		@param gesture: gesture assigned to this method
		@type gesture: InputGesture
		"""
		ui.message("%d - %s" % (self._slot, profiles[self._slot].title))

	# Translators: Method description is displayed in the NVDA gestures dialog
	@script(description="P - %s" % _("display a list of all customized voice synthesizers profiles"))
	def script_displayAllSynthProfiles(self, gesture: InputGesture) -> None:
		"""Display a list of of all configured voice synthesizers profiles and the associated languages.
		@param gesture: gesture assigned to this method
		@type gesture: InputGesture
		"""
		self.synthsProfilesDialog()

	def synthsProfilesDialog(self) -> None:
		"""Dialog for manipulation of voice synthesizers profiles.
		Call using keyboard commands or menu items.
		"""
		def handleDialogComplete(dialogResult: int) -> None:
			"""Callback function to retrieve data from the dialog."""
			if dialogResult in range(10):
				self._slot = dialogResult
		# Translators: The title of the dialog box with a list of voice synthesizers profiles
		sd = SynthesizersDialog(parent=gui.mainFrame, id=wx.ID_ANY, title=_("Voice synthesizers profiles"))
		index = max(0, sd.synthsList.FindItem(-1, str(self._slot)))
		sd.refreshProfiles()
		sd.synthsList.Focus(index)
		sd.synthsList.Select(index)
		gui.runScriptModalDialog(sd, callback=handleDialogComplete)

	# Translators: Method description is displayed in the NVDA gestures dialog
	@script(description="Del - %s" % _("delete the selected voice synthesizer profile"))
	def script_removeSynthProfile(self, gesture: InputGesture) -> None:
		"""Delete the currently selected voice synthesizer profile.
		@param gesture: gesture assigned to this method
		@type gesture: InputGesture
		"""
		slot, self._slot = self._slot, 1
		profiles.remove(slot)
		profiles.restorePrevious()
		# Translators: Message when deleting a profile
		ui.message(_("Profile %d successfully deleted") % slot)

	# Translators: Method description is displayed in the NVDA gestures dialog
	@script(description="R - %s" % _("restore default voice synthesizer"))
	def script_restoreDefaultSynth(self, gesture: InputGesture) -> None:
		"""Restore default voice synthesizer from previously saved profile.
		@param gesture: gesture assigned to this method
		@type gesture: InputGesture
		"""
		profiles.rememberCurrent()
		profile = profiles.restoreDefault()
		ui.message(profile.title)

	# Translators: Method description is displayed in the NVDA gestures dialog
	@script(description="B - %s" % _("back to previous voice synthesizer"))
	def script_restorePreviousSynth(self, gesture: InputGesture) -> None:
		"""Restore previous voice synthesizer if profile was saved before switching.
		@param gesture: gesture assigned to this method
		@type gesture: InputGesture
		"""
		current = profiles.getCurrent()
		profile = profiles.restorePrevious()
		profiles.rememberCurrent(current)
		ui.message(profile.title)

	# Translators: Method description is displayed in the NVDA gestures dialog
	@script(description="V - %s" % _("save configured voice synthesizer profile"))
	def script_saveSynthProfile(self, gesture: InputGesture) -> None:
		"""Save configured voice synthesizer profile.
		@param gesture: gesture assigned to this method
		@type gesture: InputGesture
		"""
		profiles[self._slot].update()
		profiles.save()
		# Translators: Announcing after saving synthesizer profile
		ui.message(_("Voice synthesizer profile saved successfully"))

	# Translators: Method description included in the add-on help message and NVDA input gestures dialog
	@script(description=_("From F1 to F{endgate} - select online dictionary service").format(endgate=len(services)))
	def script_selectService(self, gesture: InputGesture) -> None:
		"""Select target online service.
		@param gesture: gesture assigned to this method
		@type gesture: InputGesture
		"""
		self._gate = min(int(gesture.mainKeyName.lower().replace('f', '')), len(services))
		config.conf[_addonName]['active'] = self._gate - 1
		ui.message(': '.join([gesture.displayName, services[self._gate-1].summary]))

	# Translators: Method description included in the add-on help message and NVDA input gestures dialog
	@script(description="F - %s" % _("choose online service"))
	def script_servicesDialog(self, gesture: InputGesture) -> None:
		"""Dialog for selecting an online service from the list of available.
		@param gesture: gesture assigned to this method
		@type gesture: InputGesture
		"""
		self.chooseServiceDialog()

	def chooseServiceDialog(self) -> None:
		"""Dialog for selecting an online service from the list of available.
		Call using keyboard commands or menu items.
		"""
		# Translators: The title of the online service selection dialog and menu item
		sd = ServicesDialog(parent=gui.mainFrame, id=wx.ID_ANY, title=_("choose online service").capitalize())
		gui.runScriptModalDialog(sd)

	def translate(self, text: str, isHtml: bool=False) -> None:
		"""Retrieve the dictionary entry for the given word or phrase and display/announce the result.
		This method must always be called in a separate thread so as not to block NVDA.
		@param text: a word or phrase to look up in a dictionary
		@type text: str
		@param isHtml: a sign of whether it is necessary to display the result of work in the form of HTML page
		@type isHtml: bool
		"""
		active = config.conf[_addonName]['active']
		langs = services[active].langs
		serviceName = services[active].name
		pairs = [(self.source, self.target)]
		if self.isAutoSwap:
			if langs.isAvailable(self.target, self.source):
				pairs.append((self.target, self.source))
		for lFrom, lInto in pairs:
			translator = translateWithCaching(lFrom, lInto, text, hashForCache(active))
			if translator.error:
				translateWithCaching.cache_clear()	# reset cache when HTTP errors occur
			self._cacheInfo = str(translateWithCaching.cache_info()) # - to check the current status of the queries cache
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
			self._messages.append('%s - %s' % (langs[translator.langFrom].name, langs[translator.langTo].name))
			self._messages.append(translator.plaintext)
			message = '...'.join(self._messages)
			self._messages.clear()
			queueFunction(eventQueue, messageWithLangDetection,
				{'text': message, 'lang': translator.langTo})
		if self.isCopyToClipboard:
			api.copyToClip(translator.plaintext, notify=True)

	__addonGestures = {
		# Dictionary
		"kb:NVDA+y": "dictionaryAnnounce",
		"kb:d": "dictionaryAnnounce",
		"kb:w": "dictionaryBox",
		"kb:e": "editText",
		"kb:a": "announceLanguages",
		"kb:s": "swapLanguages",
		"kb:c": "copyLastResult",
		"kb:u": "updateLanguages",
		"kb:q": "dictionaryStatistics",
		# General
		"kb:F": "servicesDialog",
		"kb:`": "servicesDialog",
		"kb:o": "showSettings",
		"kb:h": "help",
		# Profiles of voice synthesizers
		"kb:g": "announceSelectedSynthProfile",
		"kb:p": "displayAllSynthProfiles",
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
