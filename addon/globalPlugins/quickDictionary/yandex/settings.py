# settings.py
# Contains a description of the settings panel of a specific service
# A part of the NVDA Quick Dictionary add-on
# This file is covered by the GNU General Public License.
# See the file COPYING for more details.
# Copyright (C) 2020-2021 Olexandr Gryshchenko <grisov.nvaccess@mailnull.com>

from typing import Callable, Iterator, Optional
import addonHandler
import config
import wx
from gui import guiHelper
from tones import beep
from logHandler import log
from .. import addonName
from ..service import secrets
from .api import serviceName
from .languages import ServiceLanguage, langs

try:
	addonHandler.initTranslation()
except addonHandler.AddonError:
	log.warning("Unable to init translations. This may be because the addon is running from NVDA scratchpad.")
_: Callable[[str], str]


class ServicePanel(wx.Panel):
	"""Service settings panel object."""

	def __init__(
		self,
		parent: Optional[wx.Window] = None,
		id: int = wx.ID_ANY
	) -> None:
		"""Create a settings panel for a specific service.
		Populate the service panel with settings controls.
		@param parent:
		@type parent: Optional[wx.Window]
		@param id:
		@type id: int
		"""
		super(ServicePanel, self).__init__(parent, id)
		addonHelper = guiHelper.BoxSizerHelper(self, orientation=wx.VERTICAL)
		self.SetSizer(addonHelper.sizer)
		addonHelper.addItem(
			# Translators: Help message for a dialog.
			wx.StaticText(self, label=_("Select dictionary source and target language:"), style=wx.ALIGN_LEFT)
		)
		languageHelper = guiHelper.BoxSizerHelper(self, orientation=wx.HORIZONTAL)
		self.fromChoice = languageHelper.addLabeledControl(
			# Translators: A setting in addon settings dialog.
			_("&Source language:"),
			wx.Choice,
			choices=[],
			style=wx.CB_SORT
		)
		self.intoChoice = languageHelper.addLabeledControl(
			# Translators: A setting in addon settings dialog.
			_("&Target language:"),
			wx.Choice,
			choices=[],
			style=wx.CB_SORT
		)
		addonHelper.addItem(languageHelper)
		self.widgetMaker(self.fromChoice, langs.fromList())
		self.fromChoice.Bind(wx.EVT_CHOICE, self.onSelectFrom)
		self.widgetMaker(self.intoChoice, langs.intoList(config.conf[addonName][serviceName]['from']))
		langFrom: int = self.fromChoice.FindString(langs[config.conf[addonName][serviceName]['from']].name)
		langTo: int = self.intoChoice.FindString(langs[config.conf[addonName][serviceName]['into']].name)
		self.fromChoice.Select(langFrom)
		self.intoChoice.Select(langTo)

		self.copyToClipboardChk = addonHelper.addItem(
			# Translators: A setting in addon settings dialog.
			wx.CheckBox(self, label=_("Copy dictionary response to clip&board"))
		)
		self.copyToClipboardChk.SetValue(config.conf[addonName][serviceName]['copytoclip'])
		self.autoSwapChk = addonHelper.addItem(
			# Translators: A setting in addon settings dialog.
			wx.CheckBox(self, label=_("Auto-s&wap languages"))
		)
		self.autoSwapChk.SetValue(config.conf[addonName][serviceName]['autoswap'])
		self.useMirrorChk = addonHelper.addItem(
			# Translators: A setting in addon settings dialog.
			wx.CheckBox(self, label=_("Use &alternative server"))
		)
		self.useMirrorChk.SetValue(config.conf[addonName][serviceName]['mirror'])

		# Field for input access token and link to registration
		secret = secrets[serviceName]
		tokenSizer = wx.BoxSizer(wx.HORIZONTAL)
		# Translators: A setting in addon settings dialog.
		tokenLabel = wx.StaticText(self, label=_("&Dictionary Access Token:"), style=wx.ALIGN_LEFT)
		tokenSizer.Add(tokenLabel)
		passwordSizer = wx.BoxSizer(wx.HORIZONTAL)
		self.tokenInputStars = wx.TextCtrl(
			self,
			value=secret.decode(config.conf[addonName][serviceName]['password']),
			style=wx.TE_LEFT | wx.TE_PASSWORD
		)
		passwordSizer.Add(self.tokenInputStars)
		self.tokenInputText = wx.TextCtrl(self, style=wx.TE_LEFT)
		self.tokenInputText.Hide()
		passwordSizer.Add(self.tokenInputText)
		tokenSizer.Add(passwordSizer)
		# Translators: Button label that show or hide password
		self.tokenButton = wx.Button(self, label=_("Show"))
		tokenSizer.Add(self.tokenButton)
		self.tokenButton.Bind(wx.EVT_BUTTON, self.onTokenButton)
		addonHelper.sizer.Add(tokenSizer, flag=wx.EXPAND)
		self.tokenInput = self.tokenInputStars
		self.tokenShown = False

		self.linkHref = addonHelper.addItem(
			wx.adv.HyperlinkCtrl(
				self,
				id=wx.ID_ANY,
				# Translators: A hyperlink in addon settings dialog.
				label=_("Register your own access token"),
				url=secret.url,
				style=wx.adv.HL_CONTEXTMENU | wx.adv.HL_ALIGN_RIGHT
			)
		)
		self.linkHref.Update()
		self.linkHref.Show(show=self.tokenInput.GetValue() == secret.password)
		addonHelper.sizer.Fit(self)

	def widgetMaker(self, widget: wx.Choice, languages: Iterator[ServiceLanguage]) -> None:
		"""Creating a widget based on the sequence of Language classes to display it in a wx.Choice object.
		@param widget: widget based on a sequence of Language classes
		@type widget: wx.Choice
		@param languages: list of languages available in the dictionary
		@type languages: Iterator[ServiceLanguage]
		"""
		# Translators: This displayed by default in the language selection choice list
		widget.SetLabel(_("-- select language --"))
		for lang in languages:
			widget.Append(lang.name, lang)

	def onSelectFrom(self, event: wx.PyEvent) -> None:
		"""Filling in the list of available destination languages when selecting the source language.
		@param event: event indicating the selection of an item in the wx.Choice object
		@type event: wx.PyEvent
		"""
		fromLang: str = self.fromChoice.GetClientData(self.fromChoice.GetSelection()).code
		self.intoChoice.Clear()
		self.widgetMaker(self.intoChoice, langs.intoList(fromLang))
		intoLang: int = self.intoChoice.FindString(langs[config.conf[addonName][serviceName]['into']].name)
		self.intoChoice.Select(intoLang if intoLang >= 0 else 0)

	def onTokenButton(self, event: wx.PyEvent) -> None:
		"""Toggle TextCtrl fields that show or hide the entered password.
		@param event: event that occurs when a wx.Button is pressed
		@type event: wx.PyEvent
		"""
		self.tokenShown = not self.tokenShown
		self.tokenInputText.Show(self.tokenShown)
		self.tokenInputStars.Show(not self.tokenShown)
		if self.tokenShown:
			self.tokenInputText.SetValue(self.tokenInputStars.GetValue())
			self.tokenInputText.SetFocus()
			self.tokenInput = self.tokenInputText
			# Translators: Button label that show or hide password
			self.tokenButton.SetLabel(_("Hide"))
			beep(400, 5)
		else:
			self.tokenInputStars.SetValue(self.tokenInputText.GetValue())
			self.tokenInputStars.SetFocus()
			self.tokenInput = self.tokenInputStars
			# Translators: Button label that show or hide password
			self.tokenButton.SetLabel(_("Show"))
			beep(300, 5)
		self.tokenInputText.GetParent().Layout()

	def save(self) -> None:
		"""Save the state of the service panel settings."""
		fromLang: str = self.fromChoice.GetClientData(self.fromChoice.GetSelection()).code
		intoLang: str = self.intoChoice.GetClientData(self.intoChoice.GetSelection()).code
		config.conf[addonName][serviceName]['from'] = fromLang
		config.conf[addonName][serviceName]['into'] = intoLang
		config.conf[addonName][serviceName]['copytoclip'] = self.copyToClipboardChk.GetValue()
		config.conf[addonName][serviceName]['autoswap'] = self.autoSwapChk.GetValue()
		config.conf[addonName][serviceName]['mirror'] = self.useMirrorChk.GetValue()
		config.conf[addonName][serviceName]['password'] = secrets[serviceName].encode(
			self.tokenInput.GetValue() or secrets[serviceName].password)
