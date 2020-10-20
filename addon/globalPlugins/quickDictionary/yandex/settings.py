#settings.py
# Contains a description of the settings panel of a specific service
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
from . import secret
from .dictionary import NAME, SUMMARY
from .languages import langs
from .. import _addonName, _addonSummary


class ServicePanel(wx.Panel):
	"""Service settings panel object."""

	def __init__(self, parent=None, id=wx.ID_ANY):
		"""Create a settings panel for a specific service."""
		super(ServicePanel, self).__init__(parent, id)
		"""Populate the service panel with settings controls."""
		sizer = wx.BoxSizer(wx.VERTICAL)
		self.SetSizer(sizer)
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
		self.widgetMaker(self._intoChoice, langs.intoList(config.conf[_addonName][NAME]['from']))
		sizer.Add(languageSizer, flag=wx.EXPAND)
		langFrom = self._fromChoice.FindString(langs[config.conf[_addonName][NAME]['from']].name)
		langTo = self._intoChoice.FindString(langs[config.conf[_addonName][NAME]['into']].name)
		self._fromChoice.Select(langFrom)
		self._intoChoice.Select(langTo)
		# Translators: A setting in addon settings dialog.
		self._copyToClipboardChk = wx.CheckBox(self, label=_("Copy dictionary response to clip&board"))
		self._copyToClipboardChk.SetValue(config.conf[_addonName][NAME]['copytoclip'])
		sizer.Add(self._copyToClipboardChk)
		# Translators: A setting in addon settings dialog.
		self._autoSwapChk = wx.CheckBox(self, label=_("Auto-&swap languages"))
		self._autoSwapChk.SetValue(config.conf[_addonName][NAME]['autoswap'])
		sizer.Add(self._autoSwapChk)
		# Translators: A setting in addon settings dialog.
		self._useMirrorChk = wx.CheckBox(self, label=_("Use &alternative server"))
		self._useMirrorChk.SetValue(config.conf[_addonName][NAME]['mirror'])
		sizer.Add(self._useMirrorChk)

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
		self._tokenInput.SetValue(config.conf[_addonName][NAME]['token'])
		sizer.Add(self._linkHref, flag=wx.EXPAND)
		sizer.Show(self._linkHref, show=self._tokenInput.GetValue()==secret.APIKEY)
		sizer.Fit(self)

	def widgetMaker(self, widget, languages) -> None:
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

	def onSelectFrom(self, event) -> None:
		"""Filling in the list of available destination languages when selecting the source language.
		@param event: event indicating the selection of an item in the wx.Choice object
		@type event: wx.core.PyEventBinder
		"""
		fromLang = self._fromChoice.GetClientData(self._fromChoice.GetSelection()).code
		self._intoChoice.Clear()
		self.widgetMaker(self._intoChoice, langs.intoList(fromLang))
		intoLang = self._intoChoice.FindString(langs[config.conf[_addonName][NAME]['into']].name)
		self._intoChoice.Select(intoLang if intoLang>=0 else 0)

	def save(self) -> None:
		"""Save the state of the service panel settings."""
		fromLang = self._fromChoice.GetClientData(self._fromChoice.GetSelection()).code
		intoLang = self._intoChoice.GetClientData(self._intoChoice.GetSelection()).code
		config.conf[_addonName][NAME]['from'] = fromLang
		config.conf[_addonName][NAME]['into'] = intoLang
		config.conf[_addonName][NAME]['copytoclip'] = self._copyToClipboardChk.GetValue()
		config.conf[_addonName][NAME]['autoswap'] = self._autoSwapChk.GetValue()
		config.conf[_addonName][NAME]['mirror'] = self._useMirrorChk.GetValue()
		accessToken = self._tokenInput.GetValue()
		config.conf[_addonName][NAME]['token'] = accessToken or secret.APIKEY
