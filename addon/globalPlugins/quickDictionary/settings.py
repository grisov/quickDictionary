#settings.py
# Main graphic dialogs of Quick Dictionary add-on
# A part of the NVDA Quick Dictionary add-on
# This file is covered by the GNU General Public License.
# See the file COPYING for more details.
# Copyright (C) 2020 Olexandr Gryshchenko <grisov.nvaccess@mailnull.com>

import addonHandler
from logHandler import log
try:
	addonHandler.initTranslation()
except addonHandler.AddonError:
	log.warning("Unable to initialise translations. This may be because the addon is running from NVDA scratchpad.")

import gui
from gui.nvdaControls import AutoWidthColumnListCtrl
import wx
import config
from . import _addonName, _addonSummary
from .locator import services
from .synthesizers import profiles


class QDSettingsPanel(gui.SettingsPanel):
	"""Main add-on settings panel which uses separate service panels."""
	title = _addonSummary

	def __init__(self, parent):
		"""Initializing the add-on settings panel object."""
		super(QDSettingsPanel, self).__init__(parent)

	def makeSettings(self, sizer: wx._core.BoxSizer) -> None:
		"""Populate the panel with settings controls.
		Overrides the corresponding abstract method of the gui.SettingsPanel class.
		@param sizer: The sizer to which to add the settings controls.
		@type sizer: wx._core.BoxSizer
		"""
		self._sizer = sizer
		self._active = config.conf[_addonName]['active']
		servSizer = wx.BoxSizer(wx.HORIZONTAL)
		# Translators: A setting in addon settings dialog.
		servLabel = wx.StaticText(self, label=_("Select &online service:"))
		servSizer.Add(servLabel)
		self._servChoice = wx.Choice(self, choices=[])
		servSizer.Add(self._servChoice)
		for service in services:
			self._servChoice.Append(service.summary, service)
		self._servChoice.Select(self._active)
		sizer.Add(servSizer, flag=wx.EXPAND)
		sizer.Fit(self)
		self._servChoice.Bind(wx.EVT_CHOICE, self.onSelectService)

		# Display the settings panel of the selected service
		self._container = wx.Panel(parent=self)
		self._panel = ServicePanel(self._active, parent=self._container)
		sizer.Add(self._container)
		sizer.Fit(self)

	def onSelectService(self, event) -> None:
		"""Executed when switching between services.
		@param event: event binder object that specifies the selection of an item in the wx.Choice object
		@type event: wx.core.PyEventBinder
		"""
		serv = self._servChoice.GetClientData(self._servChoice.GetSelection())
		self._active = serv.id
		event.Skip()
		self._panel.Destroy()
		self._panel = ServicePanel(self._active, parent=self._container)
		self._sizer.Fit(self)

	def postInit(self) -> None:
		"""Set system focus to service selection dropdown list.
		Overrides the corresponding abstract method of the gui.SettingsPanel class.
		"""
		self._servChoice.SetFocus()

	def onSave(self) -> None:
		"""Update Configuration when clicking OK.
		Overrides the corresponding abstract method of the gui.SettingsPanel class.
		"""
		config.conf[_addonName]['active'] = self._active
		self._panel.save()


class ServicePanel(wx.Panel):
	"""Panel wx, which during formation adds the corresponding settings panel of the selected service.
	Also adds the panel for associating voice synthesizers with languages.
	"""

	def __init__(self, active: int, parent=None, id=wx.ID_ANY):
		"""Create a panel to display in the add-on settings dialog.
		@param active: index of the selected service
		@type active: int
		"""
		super(ServicePanel, self).__init__(parent, id)
		self._active = active
		sizer = wx.BoxSizer(wx.VERTICAL)
		self.SetSizer(sizer)
		self._sizer = sizer
		self._servContainer = wx.Panel(parent=self)
		self._servPanel = services[self._active].panel(parent=self._servContainer)
		sizer.Add(self._servContainer)
		sizer.Fit(self)

		# Translators: A setting in addon settings dialog.
		self._switchSynthChk = wx.CheckBox(self, label=_("Switch between &voice synthesizers for selected languages"))
		sizer.Add(self._switchSynthChk)
		self._switchSynthChk.SetValue(config.conf[_addonName][services[self._active].name]['switchsynth'])
		self._switchSynthChk.Bind(wx.EVT_CHECKBOX, self.onSwitchSynth)

		# Display a list of voice synthesizers and the choice of languages with which they are associated
		self._synthPanel = self.synthsGrid()
		sizer.Add(self._synthPanel)
		# Blank sizer, which will be dynamically replaced by the _synthPanel block
		self._blankSizer = self.blankPanel()
		sizer.Add(self._blankSizer)
		sizer.Show(self._blankSizer, show=not self._switchSynthChk.GetValue())
		sizer.Show(self._synthPanel, show=self._switchSynthChk.GetValue())
		sizer.Fit(self)

	def synthsGrid(self) -> wx._core.BoxSizer:
		"""Build a panel with a list of profiles of voice synthesizers and associated languages.
		@return: formed BoxSizer object
		@rtype: wx._core.BoxSizer
		"""
		sizer = wx.BoxSizer(wx.VERTICAL)
		# Output of the list of synthesizers for language binding
		synthSizer = wx.GridSizer(cols=0, vgap=1, hgap=3)
		self._synthLangsChoice = {}
		if not next(iter(profiles), None):
			# Translators: A warning in addon settings dialog.
			synthWarning = wx.TextCtrl(self, value=_("Please set up voice synthesizers profiles."), size=(200, 30),
				style=wx.TE_READONLY | wx.TE_MULTILINE | wx.TE_NO_VSCROLL | wx.TE_CENTER | wx.TE_PROCESS_TAB)
			synthSizer.Add(synthWarning, proportion=wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_CENTER_VERTICAL, flag=wx.EXPAND)
		else:
			synthSizer.SetCols(2)
			synthSizer.SetRows(len(profiles))
			synthLabel = {}
			for slot, profile in profiles:
				synthLabel[slot] = wx.StaticText(self, label="&%d. %s:" % (slot, profile.title), style=wx.ALIGN_RIGHT)
				self._synthLangsChoice[slot] = wx.Choice(self, choices=[], style=wx.CB_SORT)
				synthSizer.Add(synthLabel[slot], proportion=wx.ALIGN_RIGHT)
				synthSizer.Add(self._synthLangsChoice[slot], proportion=wx.ALIGN_LEFT)
		sizer.Add(synthSizer, proportion=wx.ALIGN_CENTER_HORIZONTAL, border=wx.ALL)
		sizer.Fit(self)

		# Setting initial values in choices and interaction between choices
		langs = services[self._active].langs
		self._langs = [langs['']] + [l for l in langs.all]
		self._choices = dict({slot: profile.lang for slot, profile in profiles})
		for slot, profile in profiles:
			self.widgetMakerExclude(self._synthLangsChoice[slot], slot)
			item = self._synthLangsChoice[slot].FindString(langs[profile.lang].name)
			if item<0:
				item = self._synthLangsChoice[slot].FindString(langs[''].name)
			self._synthLangsChoice[slot].Select(item)
			self._synthLangsChoice[slot].Bind(wx.EVT_CHOICE, lambda evt, sl=slot: self.onSelectSynthLang(evt, sl))
		return sizer

	def blankPanel(self) -> wx._core.BoxSizer:
		"""Empty panel required for correct dynamic display of the hidden panel with the list of synthesizers.
		@return: BoxSizer is filled with blank lines equal to the number of voice synthesizer profiles
		@rtype: wx._core.BoxSizer
		"""
		blankSizer = wx.BoxSizer(wx.VERTICAL)
		blankLabel = wx.StaticText(self, label="\n"*len(profiles))
		blankSizer.Add(blankLabel)
		return blankSizer

	def onSwitchSynth(self, event) -> None:
		"""Executed when enable or disable the check box for switching voice synthesizers to selected languages.
		@param event: event binder object that specifies the check or uncheck the wx.CheckBox
		@type event: wx.core.PyEventBinder
		"""
		event.Skip()
		self._sizer.Show(self._blankSizer, show=not self._switchSynthChk.GetValue())
		self._sizer.Show(self._synthPanel, show=self._switchSynthChk.GetValue())
		self._sizer.Fit(self)
		self._sizer.Layout()

	def widgetMakerExclude(self, widget, slot: int) -> None:
		"""Creating a widget based on the sequence of Language classes to display it in a wx.Choice object.
		Exclude from current Choice menu items selected in other Choices.
		@param widget: widget based on a sequence of Language classes
		@type widget: wx.Choice
		@param slot: a number that identifies the current profile of the speech synthesizer
		@type slot: int
		"""
		for lang in self._langs:
			if lang.code not in [l for s,l in self._choices.items() if l and s!=slot]:
				widget.Append(lang.name, lang)

	def onSelectSynthLang(self, event, slot: int):
		"""Fill in the linked Choices and set the initial values.
		Executed when select a language from a list for one of the voice synthesizers profiles.
		@param event: event binder object that specifies the selection of an item in the wx.Choice object
		@type event: wx.core.PyEventBinder
		@param slot: a number that identifies the current profile of the speech synthesizer
		@type slot: int
		"""
		langs = services[self._active].langs
		choice = self._synthLangsChoice[slot].GetClientData(self._synthLangsChoice[slot].GetSelection())
		self._choices[slot] = choice.code
		for sl,prof in profiles:
			if sl != slot:
				self._synthLangsChoice[sl].Clear()
				self.widgetMakerExclude(self._synthLangsChoice[sl], sl)
				item = self._synthLangsChoice[sl].FindString(langs[self._choices[sl]].name)
				if item<0:
					item = self._synthLangsChoice[sl].FindString(langs[''].name)
				self._synthLangsChoice[sl].Select(item)

	def save(self) -> None:
		"""Save the state of the panel settings."""
		self._servPanel.save()
		config.conf[_addonName][services[self._active].name]['switchsynth'] = self._switchSynthChk.GetValue()
		if self._switchSynthChk.GetValue():
			for slot, profile in profiles:
				profiles[slot].lang = self._choices[slot]
			profiles.save()


class SynthesizersDialog(wx.Dialog):
	"""A dialog box that allows to manipulate the profiles of voice synthesizers."""

	def __init__(self, parent, id: int, title: str, *args, **kwargs):
		"""Create a dialog box for manipulating voice synthesizers profiles.
		@param parent: parent top level window
		@type parent: wx._core.Dialog
		@param id: identifier of the window
		@type id: int
		@param title: title of the window
		@type title: str
		"""
		super(SynthesizersDialog, self).__init__(parent, id, title=title, *args, **kwargs)
		sizer = self.sizer = wx.BoxSizer(wx.VERTICAL)
		sHelper = gui.guiHelper.BoxSizerHelper(self, sizer=sizer)
		self.synthsList = sHelper.addLabeledControl(
			# Translators: The label in dialog with the list of voice synthesizers profiles
			_("Select a voice synthesizer &profile from the list"),
			AutoWidthColumnListCtrl,
			autoSizeColumn=1, # The replacement column is likely to need the most space
			itemTextCallable=None,
			style=wx.LC_REPORT | wx.LC_SINGLE_SEL
		)
		# Translators: The label for a column in the list of voice synthesizers profiles
		self.synthsList.InsertColumn(0, _("Slot"), width=30)
		# Translators: The label for a column in the list of voice synthesizers profiles
		self.synthsList.InsertColumn(1, _("Voice synthesizer"))
		# Translators: The label for a column in the list of voice synthesizers profiles
		self.synthsList.InsertColumn(2, _("Associated language"), width=120)

		# Translators: The message that is displayed when the configured synthesizers profiles are missing
		self.synthsWarning = wx.TextCtrl(self, value=_("Please set up voice synthesizers profiles."), size=(200, 30),
			style=wx.TE_READONLY | wx.TE_MULTILINE | wx.TE_NO_VSCROLL | wx.TE_CENTER | wx.TE_PROCESS_TAB)
		sizer.Add(self.synthsWarning, proportion=wx.ALIGN_TOP, flag=wx.EXPAND)

		# A number of buttons at the bottom of the dialog box
		buttons = wx.BoxSizer(wx.HORIZONTAL)
		# Translators: Label of the button that activates the selected voice synthesizer profile
		self.activateButton = wx.Button(self, label=_("&Activate"))
		buttons.Add(self.activateButton)
		# Translators: Label of the button that opens the dialog for changing the selected profile
		self.changeButton = wx.Button(self, label=_("&Change"))
		buttons.Add(self.changeButton)
		self.deleteButton = wx.Button(self, id=wx.ID_DELETE)
		buttons.Add(self.deleteButton)
		refreshButton = wx.Button(self, id=wx.ID_REFRESH)
		buttons.Add(refreshButton)
		saveButton = wx.Button(self, id=wx.ID_SAVE)
		buttons.Add(saveButton)
		cancelButton = wx.Button(self, id=wx.ID_CANCEL)
		buttons.Add(cancelButton)
		sizer.Add(buttons, flag=wx.BOTTOM)
		sizer.Fit(self)
		self.SetSizer(sizer)
		self.Center(wx.BOTH | wx.Center)
		self.displayContent()

		# Binding dialog box elements to handler methods
		self.synthsList.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.onActivateProfile)
		self.activateButton.Bind(wx.EVT_BUTTON, self.onActivateProfile)
		self.changeButton.Bind(wx.EVT_BUTTON, handler=lambda evt: self.changeProfile())
		self.deleteButton.Bind(wx.EVT_BUTTON, handler=lambda evt: self.deleteProfile())
		refreshButton.Bind(wx.EVT_BUTTON, handler=lambda evt: self.refreshProfiles())
		saveButton.Bind(wx.EVT_BUTTON, handler=lambda evt: self.saveProfiles())
		self.Bind(wx.EVT_CHAR_HOOK, self.onKeyPress)

	def displayContent(self) -> None:
		"""Display a list of voice synthesizers profiles if the list is not empty,
		otherwise, a message about the absence of saved profiles is displayed.
		"""
		if len(profiles)>0:
			self.synthsWarning.Hide()
			self.synthsList.Show()
			self.activateButton.Show()
			self.changeButton.Show()
			self.deleteButton.Show()
			self.fillInList()
			self.synthsList.SetFocus()
		else:
			self.synthsList.Hide()
			self.activateButton.Hide()
			self.changeButton.Hide()
			self.deleteButton.Hide()
			self.synthsWarning.Show()
			self.synthsWarning.SetFocus()
		self.sizer.Layout()

	def fillInList(self) -> None:
		"""Display a list of saved synthesizers profiles in the ListCtrl widget."""
		langs = services[config.conf[_addonName]['active']].langs
		self.synthsList.DeleteAllItems()
		for slot,profile in profiles:
			self.synthsList.Append((slot, profile.title, langs[profile.lang].name))
		if len(profiles)>0:
			self.synthsList.Focus(0)
			self.synthsList.Select(0)

	def deleteProfile(self) -> None:
		"""Delete selected voice synthesizer profile."""
		if len(profiles)==0:
			return
		item = int(self.synthsList.GetItem(itemIdx=self.synthsList.GetFocusedItem(), col=0).GetText())
		profiles.remove(item)
		self.displayContent()
		# Translators: Message that displayed after deleting the profile (also this is the script description)
		gui.messageBox(message=_("Profile %d successfully deleted") % item, caption=_("delete the selected voice synthesizer profile").capitalize(), parent=self)

	def changeProfile(self) -> None:
		"""Open dialog for changing selected voice synthesizer profile."""
		if len(profiles)==0:
			return
		item = int(self.synthsList.GetItem(itemIdx=self.synthsList.GetFocusedItem(), col=0).GetText())
		profiles[item].set()
		wx.CallAfter(gui.mainFrame.onSpeechSettingsCommand, None)
		# ***
		#profiles[item].update()
		#self.displayContent()

	def refreshProfiles(self) -> None:
		"""Update the list of saved voice synthesizers profiles on the screen."""
		profiles.load()
		self.displayContent()

	def saveProfiles(self) -> None:
		"""Save a list of voice synthesizers profiles."""
		# Translators: Display the message after saving the voice synthesizers profiles
		message = _("Voice synthesizer profile saved successfully") if profiles.save() else _("Profiles list could not be saved")
		# Translators: The title of the messageBox that appears after saving the list of voice synthesizers profiles
		gui.messageBox(message=message, caption=_("Saving voice synthesizers profiles list"), parent=self)

	def onKeyPress(self, event) -> None:
		"""Performed when pressing keys.
		@param event: event binder object that handles keystrokes
		@type event: wx.core.PyEventBinder
		"""
		{
			wx.WXK_DELETE: self.deleteProfile,
			wx.WXK_F5: self.refreshProfiles,
			wx.WXK_F2: self.saveProfiles
		}.get(event.GetKeyCode(), lambda: None)()
		event.Skip()

	def onActivateProfile(self, event) -> None:
		"""Activation of the selected voice synthesizer profile.
		The profile slot number is passed to the external handler.
		@param event: event binder object that handles the activation of the button or ListItem element
		@type event: wx.core.PyEventBinder
		"""
		event.Skip()
		item = int(self.synthsList.GetItem(itemIdx=self.synthsList.GetFocusedItem(), col=0).GetText())
		profiles[item].set()
		self.EndModal(item)
