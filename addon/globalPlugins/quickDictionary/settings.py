#settings.py
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
from .languages import langs
from .synthesizers import profiles
from .secret import APIKEY as TOKEN


class QuickDictionarySettingsPanel(gui.SettingsPanel):
	"""Add-on settings panel object"""
	title = _addonSummary

	def __init__(self, parent):
		"""Initializing the add-on settings panel object"""
		super(QuickDictionarySettingsPanel, self).__init__(parent)

	def makeSettings(self, sizer: wx._core.BoxSizer):
		"""Populate the panel with settings controls.
		@param sizer: The sizer to which to add the settings controls.
		@type sizer: wx._core.BoxSizer
		"""
		# Translators: Help message for a dialog.
		helpLabel = wx.StaticText(self, label=_("Select dictionary source and target language:"), style=wx.ALIGN_LEFT)
		helpLabel.Wrap(helpLabel.GetSize()[0])
		sizer.Add(helpLabel, flag=wx.EXPAND)
		languageSizer = wx.BoxSizer(wx.HORIZONTAL)
		fromSizer = wx.BoxSizer(wx.HORIZONTAL)
		# Translators: A setting in addon settings dialog.
		fromLabel = wx.StaticText(self, label=_("&Source language:"))
		fromSizer.Add(fromLabel)
		self._fromChoice = wx.Choice(self, choices=[], style=wx.CB_SORT)
		fromSizer.Add(self._fromChoice)
		languageSizer.Add(fromSizer)
		intoSizer = wx.BoxSizer(wx.HORIZONTAL)
		# Translators: A setting in addon settings dialog.
		intoLabel = wx.StaticText(self, label=_("&Target language:"))
		intoSizer.Add(intoLabel)
		self._intoChoice = wx.Choice(self, choices=[], style=wx.CB_SORT)
		intoSizer.Add(self._intoChoice)
		languageSizer.Add(intoSizer)
		self.widgetMaker(self._fromChoice, langs.fromList())
		self._fromChoice.Bind(wx.EVT_CHOICE, self.onSelectFrom)
		self.widgetMaker(self._intoChoice, langs.intoList(config.conf[_addonName]['from']))
		sizer.Add(languageSizer, flag=wx.EXPAND)
		langFrom = self._fromChoice.FindString(langs[config.conf[_addonName]['from']].name)
		langTo = self._intoChoice.FindString(langs[config.conf[_addonName]['into']].name)
		self._fromChoice.Select(langFrom)
		self._intoChoice.Select(langTo)
		# Translators: A setting in addon settings dialog.
		self._copyToClipboardChk = wx.CheckBox(self, label=_("Copy dictionary response to clip&board"))
		self._copyToClipboardChk.SetValue(config.conf[_addonName]['copytoclip'])
		sizer.Add(self._copyToClipboardChk)
		# Translators: A setting in addon settings dialog.
		self._autoSwapChk = wx.CheckBox(self, label=_("Auto-&swap languages"))
		self._autoSwapChk.SetValue(config.conf[_addonName]['autoswap'])
		sizer.Add(self._autoSwapChk)
		# Translators: A setting in addon settings dialog.
		self._useMirrorChk = wx.CheckBox(self, label=_("Use &alternative server"))
		self._useMirrorChk.SetValue(config.conf[_addonName]['mirror'])
		sizer.Add(self._useMirrorChk)

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

		# Field for input access token and link to registration
		tokenSizer = wx.BoxSizer(wx.HORIZONTAL)
		# Translators: A setting in addon settings dialog.
		tokenLabel = wx.StaticText(self, label=_("&Dictionary Access Token:"), style=wx.ALIGN_LEFT)
		tokenSizer.Add(tokenLabel)
		self._tokenInput = wx.TextCtrl(self, style=wx.TE_LEFT)
		tokenSizer.Add(self._tokenInput)
		sizer.Add(tokenSizer, flag=wx.EXPAND)
		url = 'https://yandex.com/dev/dictionary/keys/get/'
		# Translators: A setting in addon settings dialog.
		self._linkHref = wx.adv.HyperlinkCtrl(self, -1, label=_("Register your own access token"), url=url, style=wx.adv.HL_CONTEXTMENU | wx.adv.HL_DEFAULT_STYLE | wx.adv.HL_ALIGN_RIGHT)
		self._linkHref.Update()
		self._tokenInput.SetValue(config.conf[_addonName]['token'])
		sizer.Add(self._linkHref, flag=wx.EXPAND)
		sizer.Show(self._linkHref, show=self._tokenInput.GetValue()==TOKEN)

	def widgetMaker(self, widget, languages):
		"""Creating a widget based on the sequence of Language classes to display it in a wx.Choice object.
		@param widget: widget based on a sequence of Language classes
		@type widget: wx.Choice
		@param languages: list of languages available in the dictionary
		@type languages: languages.Languages
		"""
		# Translators: This displayed by default in the language selection choice list
		widget.SetLabel(_("-- select language --"))
		for lang in languages:
			widget.Append(lang.name, lang)

	def onSelectFrom(self, event):
		"""Filling in the list of available destination languages when selecting the source language.
		@param event: event indicating the selection of an item in the wx.Choice object
		@type event: wx.core.PyEventBinder
		"""
		fromLang = self._fromChoice.GetClientData(self._fromChoice.GetSelection()).code
		self._intoChoice.Clear()
		self.widgetMaker(self._intoChoice, langs.intoList(fromLang))
		intoLang = self._intoChoice.FindString(langs[config.conf[_addonName]['into']].name)
		self._intoChoice.Select(intoLang if intoLang>=0 else 0)

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

	def postInit(self):
		"""Set system focus to source language selection dropdown list."""
		self._fromChoice.SetFocus()

	def onSave(self):
		"""Update Configuration when clicking OK."""
		fromLang = self._fromChoice.GetClientData(self._fromChoice.GetSelection()).code
		intoLang = self._intoChoice.GetClientData(self._intoChoice.GetSelection()).code
		config.conf[_addonName]['from'] = fromLang
		config.conf[_addonName]['into'] = intoLang
		config.conf[_addonName]['copytoclip'] = self._copyToClipboardChk.GetValue()
		config.conf[_addonName]['autoswap'] = self._autoSwapChk.GetValue()
		config.conf[_addonName]['mirror'] = self._useMirrorChk.GetValue()
		config.conf[_addonName]['switchsynth'] = self._switchSynthChk.GetValue()
		accessToken = self._tokenInput.GetValue()
		config.conf[_addonName]['token'] = accessToken if accessToken else TOKEN
		if config.conf[_addonName]['switchsynth']:
			for slot, profile in profiles:
				profiles[slot].lang = self._choices[slot]
			profiles.save()
