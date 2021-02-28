#settings.py
# Contains a description of the settings panel of a specific service
# A part of the NVDA Quick Dictionary add-on
# This file is covered by the GNU General Public License.
# See the file COPYING for more details.
# Copyright (C) 2020-2021 Olexandr Gryshchenko <grisov.nvaccess@mailnull.com>

from typing import Callable
import addonHandler
from logHandler import log
try:
	addonHandler.initTranslation()
except addonHandler.AddonError:
	log.warning("Unable to initialise translations. This may be because the addon is running from NVDA scratchpad.")
_: Callable[[str], str]

import gui
import wx
import config
from tones import beep
from .. import _addonName
from ..service import secrets
from .api import serviceName
from .languages import langs


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
		self.widgetMaker(self._intoChoice, langs.intoList(config.conf[_addonName][serviceName]['from']))
		sizer.Add(languageSizer, flag=wx.EXPAND)
		langFrom = self._fromChoice.FindString(langs[config.conf[_addonName][serviceName]['from']].name)
		langTo = self._intoChoice.FindString(langs[config.conf[_addonName][serviceName]['into']].name)
		self._fromChoice.Select(langFrom)
		self._intoChoice.Select(langTo)
		# Translators: A setting in addon settings dialog.
		self._copyToClipboardChk = wx.CheckBox(self, label=_("Copy dictionary response to clip&board"))
		self._copyToClipboardChk.SetValue(config.conf[_addonName][serviceName]['copytoclip'])
		sizer.Add(self._copyToClipboardChk)
		# Translators: A setting in addon settings dialog.
		self._autoSwapChk = wx.CheckBox(self, label=_("Auto-s&wap languages"))
		self._autoSwapChk.SetValue(config.conf[_addonName][serviceName]['autoswap'])
		sizer.Add(self._autoSwapChk)
		# Translators: A setting in addon settings dialog.
		self._useMirrorChk = wx.CheckBox(self, label=_("Use &alternative server"))
		self._useMirrorChk.SetValue(config.conf[_addonName][serviceName]['mirror'])
		sizer.Add(self._useMirrorChk)

		# Field for input access token and link to registration
		secret = secrets[serviceName]
		tokenSizer = wx.BoxSizer(wx.HORIZONTAL)
		# Translators: A setting in addon settings dialog.
		tokenLabel = wx.StaticText(self, label=_("&Dictionary Access Token:"), style=wx.ALIGN_LEFT)
		tokenSizer.Add(tokenLabel)
		passwordSizer = wx.BoxSizer(wx.HORIZONTAL)
		self._tokenInputStars = wx.TextCtrl(self, value=secret.decode(config.conf[_addonName][serviceName]['password']), style=wx.TE_LEFT | wx.TE_PASSWORD)
		passwordSizer.Add(self._tokenInputStars)
		self._tokenInputText = wx.TextCtrl(self, style=wx.TE_LEFT)
		self._tokenInputText.Hide()
		passwordSizer.Add(self._tokenInputText)
		tokenSizer.Add(passwordSizer)
		# Translators: Button label that show or hide password
		self._tokenButton= wx.Button(self, label=_("Show"))
		tokenSizer.Add(self._tokenButton)
		self._tokenButton.Bind(wx.EVT_BUTTON, self.onTokenButton)
		sizer.Add(tokenSizer, flag=wx.EXPAND)
		self._tokenInput = self._tokenInputStars
		self._tokenShown = False

		# Translators: A setting in addon settings dialog.
		self._linkHref = wx.adv.HyperlinkCtrl(self, -1, label=_("Register your own access token"), url=secret.url, style=wx.adv.HL_CONTEXTMENU | wx.adv.HL_DEFAULT_STYLE | wx.adv.HL_ALIGN_RIGHT)
		self._linkHref.Update()
		sizer.Add(self._linkHref, flag=wx.EXPAND)
		sizer.Show(self._linkHref, show=self._tokenInput.GetValue()==secret.password)
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
		intoLang = self._intoChoice.FindString(langs[config.conf[_addonName][serviceName]['into']].name)
		self._intoChoice.Select(intoLang if intoLang>=0 else 0)

	def onTokenButton(self, event) -> None:
		"""Toggle TextCtrl fields that show or hide the entered password.
		@param event: event that occurs when a wx.Button is pressed
		@type event: wx.core.PyEventBinder
		"""
		self._tokenShown = not self._tokenShown
		self._tokenInputText.Show(self._tokenShown)
		self._tokenInputStars.Show(not self._tokenShown)
		if self._tokenShown:
			self._tokenInputText.SetValue(self._tokenInputStars.GetValue())
			self._tokenInputText.SetFocus()
			self._tokenInput = self._tokenInputText
			# Translators: Button label that show or hide password
			self._tokenButton.SetLabel(_("Hide"))
			beep(400, 5)
		else:
			self._tokenInputStars.SetValue(self._tokenInputText.GetValue())
			self._tokenInputStars.SetFocus()
			self._tokenInput = self._tokenInputStars
			# Translators: Button label that show or hide password
			self._tokenButton.SetLabel(_("Show"))
			beep(300, 5)
		self._tokenInputText.GetParent().Layout()

	def save(self) -> None:
		"""Save the state of the service panel settings."""
		fromLang = self._fromChoice.GetClientData(self._fromChoice.GetSelection()).code
		intoLang = self._intoChoice.GetClientData(self._intoChoice.GetSelection()).code
		config.conf[_addonName][serviceName]['from'] = fromLang
		config.conf[_addonName][serviceName]['into'] = intoLang
		config.conf[_addonName][serviceName]['copytoclip'] = self._copyToClipboardChk.GetValue()
		config.conf[_addonName][serviceName]['autoswap'] = self._autoSwapChk.GetValue()
		config.conf[_addonName][serviceName]['mirror'] = self._useMirrorChk.GetValue()
		config.conf[_addonName][serviceName]['password'] = secrets[serviceName].encode(self._tokenInput.GetValue() or secrets[serviceName].password)
