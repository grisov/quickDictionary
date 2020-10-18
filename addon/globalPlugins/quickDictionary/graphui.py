#graphui.py
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
import gui
import wx
import config
from . import _addonName, _addonSummary
from .locator import services
from .synthesizers import profiles

langs = services[config.conf[_addonName]['active']].langs


class QDSettingsPanel(gui.SettingsPanel):
	"""General add-on settings panel object for inheritance in services."""

	def __init__(self, parent):
		"""Initializing the add-on settings panel object"""
		super(QDSettingsPanel, self).__init__(parent)

	def makeAssociateSynths(self, sizer: wx._core.BoxSizer):
		"""Create a settings block to associate voice synthesizer profiles with languages.
		@param sizer: The sizer to which to add the settings controls.
		@type sizer: wx._core.BoxSizer
		"""
		# Translators: A setting in addon settings dialog.
		self._switchSynthChk = wx.CheckBox(self, label=_("Switch between &voice synthesizers for selected languages"))
		sizer.Add(self._switchSynthChk)

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
				synthSizer.Add(synthLabel[slot], wx.ALIGN_RIGHT)
				synthSizer.Add(self._synthLangsChoice[slot], proportion=wx.ALIGN_LEFT)
		sizer.Add(synthSizer, proportion=wx.ALIGN_CENTER_HORIZONTAL, border=wx.ALL)
		self._switchSynthChk.Bind(wx.EVT_CHECKBOX, lambda evt, sizer=sizer, synthSizer=synthSizer: sizer.Show(synthSizer, show=evt.IsChecked()) and sizer.Layout())
		self._switchSynthChk.SetValue(config.conf[_addonName]['switchsynth'])
		sizer.Show(synthSizer, show=self._switchSynthChk.GetValue())

		# Setting initial values in choices and interaction between choices
		self._langs = [langs['']] + [l for l in langs.fromList()]
		self._choices = dict({slot: profile.lang for slot, profile in profiles})
		for slot, profile in profiles:
			self.widgetMakerExclude(self._synthLangsChoice[slot], slot)
			item = self._synthLangsChoice[slot].FindString(langs[profile.lang].name)
			if item<0:
				item = self._synthLangsChoice[slot].FindString(langs[''].name)
			self._synthLangsChoice[slot].Select(item)
			self._synthLangsChoice[slot].Bind(wx.EVT_CHOICE, lambda evt, sl=slot: self.onSelectSynthLang(evt, sl))

	def widgetMakerExclude(self, widget, slot: int):
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
		@param event: event indicating the selection of an item in the wx.Choice object
		@type event: wx.core.PyEventBinder
		@param slot: a number that identifies the current profile of the speech synthesizer
		@type slot: int
		"""
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

	def onSave(self):
		"""Update Configuration when clicking OK."""
		config.conf[_addonName]['switchsynth'] = self._switchSynthChk.GetValue()
		if config.conf[_addonName]['switchsynth']:
			for slot, profile in profiles:
				profiles[slot].lang = self._choices[slot]
			profiles.save()


# Template for displaying HTML content.
htmlTemplate = ''.join(["&nbsp;",
	"<!DOCTYPE html>",
	"<html>",
	"<head>",
	'<meta http-equiv="Content-Type" content="text/html; charset=utf-8">',
	"<title></title>"
	'<link rel="stylesheet" type="text/css" href="%s">' % os.path.join(os.path.dirname(__file__), 'style.css'),
	"</head>",
	"<body>{body}</body>",
	"</html>"
])
