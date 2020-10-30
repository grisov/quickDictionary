#settings.py
# Main graphic dialogs of Quick Dictionary add-on
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

import gui
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

		if self._switchSynthChk.GetValue():
			self._synthPanel = AssociateSynthPanel(self._active, parent=self)
		else:
			self._synthPanel = wx.StaticText(parent=self)
		sizer.Add(self._synthPanel)
		sizer.Fit(self)

	def onSwitchSynth(self, event) -> None:
		"""Executed when enable or disable the check box for switching voice synthesizers to selected languages.
		@param event: event binder object that specifies the check or uncheck the wx.CheckBox
		@type event: wx.core.PyEventBinder
		"""
		event.Skip()
		self._synthPanel.Destroy()
		if self._switchSynthChk.GetValue():
			self._synthPanel = AssociateSynthPanel(self._active, parent=self)
		else:
			self._synthPanel = wx.StaticText(parent=self)
		self._sizer.Fit(self)
		#self._synthPanel.GetParent().Layout()

	def save(self) -> None:
		"""Save the state of the panel settings."""
		self._servPanel.save()
		config.conf[_addonName][services[self._active].name]['switchsynth'] = self._switchSynthChk.GetValue()
		if self._switchSynthChk.GetValue():
			self._synthPanel.save()


class AssociateSynthPanel(wx.Panel):
	"""Panel of association of voice synthesizers with selected languages."""

	def __init__(self, active: int, parent=None, id=wx.ID_ANY):
		"""Create a settings block to associate voice synthesizer profiles with languages.
		@param active: index of the selected service
		@type active: int
		"""
		super(AssociateSynthPanel, self).__init__(parent, id)
		self._active = active
		sizer = wx.BoxSizer(wx.VERTICAL)
		self.SetSizer(sizer)
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
		for slot, profile in profiles:
			profiles[slot].lang = self._choices[slot]
		profiles.save()
