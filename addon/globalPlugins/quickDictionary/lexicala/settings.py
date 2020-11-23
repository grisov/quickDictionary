#settings.py
# Contains a description of the settings panel of a specific service
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
import wx
import config
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
		sourceSizer = wx.BoxSizer(wx.HORIZONTAL)
		# Translators: A setting in addon settings dialog.
		sourceLabel = wx.StaticText(self, label=_("&Dictionary:"))
		sourceSizer.Add(sourceLabel)
		self._sourceChoice = wx.Choice(self, choices=langs.sources, style=wx.CB_SORT)
		sourceSizer.Add(self._sourceChoice)
		sizer.Add(sourceSizer)
		currentSource = self._sourceChoice.FindString(config.conf[_addonName][serviceName]['source'])
		self._sourceChoice.Select(currentSource)
		self._sourceChoice.Bind(wx.EVT_CHOICE, self.onSelectSource)

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
		self.widgetMaker(self._fromChoice, langs.fromList(source=config.conf[_addonName][serviceName]['source']))
		self.widgetMaker(self._intoChoice, langs.intoList(source=config.conf[_addonName][serviceName]['source']))
		sizer.Add(languageSizer, flag=wx.EXPAND)
		langFrom = self._fromChoice.FindString(langs[config.conf[_addonName][serviceName]['from']].name)
		langTo = self._intoChoice.FindString(langs[config.conf[_addonName][serviceName]['into']].name)
		self._fromChoice.Select(langFrom)
		self._intoChoice.Select(langTo)

		# Translators: A setting in addon settings dialog.
		self._morphChk = wx.CheckBox(self, label=_("Search in both headwords and &inflections"))
		self._morphChk.SetValue(config.conf[_addonName][serviceName]['morph'])
		sizer.Add(self._morphChk)
		# Translators: A setting in addon settings dialog.
		self._analyzedChk = wx.CheckBox(self, label=_("St&rip words to their stem"))
		self._analyzedChk.SetValue(config.conf[_addonName][serviceName]['analyzed'])
		sizer.Add(self._analyzedChk)
		# Translators: A setting in addon settings dialog.
		self._allChk = wx.CheckBox(self, label=_("Show a&ll available translations"))
		self._allChk.SetValue(config.conf[_addonName][serviceName]['all'])
		sizer.Add(self._allChk)
		# Translators: A setting in addon settings dialog.
		self._copyToClipboardChk = wx.CheckBox(self, label=_("Copy dictionary response to clip&board"))
		self._copyToClipboardChk.SetValue(config.conf[_addonName][serviceName]['copytoclip'])
		sizer.Add(self._copyToClipboardChk)
		# Translators: A setting in addon settings dialog.
		self._autoSwapChk = wx.CheckBox(self, label=_("Auto-s&wap languages"))
		self._autoSwapChk.SetValue(config.conf[_addonName][serviceName]['autoswap'])
		sizer.Add(self._autoSwapChk)

		# Field for input user credentials and link to registration
		secret = secrets[serviceName]
		authSizer = wx.BoxSizer(wx.HORIZONTAL)
		userSizer = wx.BoxSizer(wx.HORIZONTAL)
		# Translators: A setting in addon settings dialog.
		nameLabel = wx.StaticText(self, label=_("&Username:"), style=wx.ALIGN_LEFT)
		userSizer.Add(nameLabel)
		self._usernameInput = wx.TextCtrl(self, value=secret.decode(config.conf[_addonName][serviceName]['username']), style=wx.TE_LEFT)
		userSizer.Add(self._usernameInput)
		authSizer.Add(userSizer)
		passwordSizer = wx.BoxSizer(wx.HORIZONTAL)
		# Translators: A setting in addon settings dialog.
		passwordLabel = wx.StaticText(self, label=_("&Password:"), style=wx.ALIGN_LEFT)
		passwordSizer.Add(passwordLabel)
		self._passwordInput = wx.TextCtrl(self, value=secret.decode(config.conf[_addonName][serviceName]['password']), style=wx.TE_LEFT | wx.TE_PASSWORD)
		passwordSizer.Add(self._passwordInput)
		authSizer.Add(passwordSizer)
		sizer.Add(authSizer)

		# Translators: A setting in addon settings dialog.
		self._linkHref = wx.adv.HyperlinkCtrl(self, -1, label=_("Register your own access token"), url=secret.url, style=wx.adv.HL_CONTEXTMENU | wx.adv.HL_DEFAULT_STYLE | wx.adv.HL_ALIGN_RIGHT)
		self._linkHref.Update()
		sizer.Add(self._linkHref, flag=wx.EXPAND)
		sizer.Show(self._linkHref, show=self._usernameInput.GetValue()==secret.username and self._passwordInput.GetValue()==secret.password)
		sizer.Fit(self)

	def onSelectSource(self, event):
		"""Fill in the lists of source and target languages when selecting source dictionary.
		@param event: event indicating the selection of an item in the wx.Choice object
		@type event: wx.core.PyEventBinder
		"""
		source = event.GetString()
		self._fromChoice.Clear()
		self.widgetMaker(self._fromChoice, langs.fromList(source=source))
		self._intoChoice.Clear()
		self.widgetMaker(self._intoChoice, langs.intoList(source=source))
		langFrom = self._fromChoice.FindString(langs[config.conf[_addonName][serviceName]['from']].name)
		langTo = self._intoChoice.FindString(langs[config.conf[_addonName][serviceName]['into']].name)
		langFrom = max(0, langFrom)
		langTo = max(0, langTo)
		self._fromChoice.Select(langFrom)
		self._intoChoice.Select(langTo)

	def widgetMaker(self, widget, languages) -> None:
		"""Creating a widget based on the sequence of Language classes to display it in a wx.Choice object.
		@param widget: widget based on a sequence of Language classes
		@type widget: wx.Choice
		@param languages: list of languages available in the dictionary
		@type languages: languages.Languages
		"""
		for lang in languages:
			widget.Append(lang.name, lang)

	def save(self) -> None:
		"""Save the state of the service panel settings."""
		config.conf[_addonName][serviceName]['source'] = self._sourceChoice.GetString(self._sourceChoice.GetSelection())
		fromLang = self._fromChoice.GetClientData(self._fromChoice.GetSelection()).code
		intoLang = self._intoChoice.GetClientData(self._intoChoice.GetSelection()).code
		config.conf[_addonName][serviceName]['from'] = fromLang
		config.conf[_addonName][serviceName]['into'] = intoLang
		config.conf[_addonName][serviceName]['morph'] = self._morphChk.GetValue()
		config.conf[_addonName][serviceName]['analyzed'] = self._analyzedChk.GetValue()
		config.conf[_addonName][serviceName]['all'] = self._allChk.GetValue()
		config.conf[_addonName][serviceName]['copytoclip'] = self._copyToClipboardChk.GetValue()
		config.conf[_addonName][serviceName]['autoswap'] = self._autoSwapChk.GetValue()
		config.conf[_addonName][serviceName]['username'] = secrets[serviceName].encode(self._usernameInput.GetValue() or secrets[serviceName].username)
		config.conf[_addonName][serviceName]['password'] = secrets[serviceName].encode(self._passwordInput.GetValue() or secrets[serviceName].password)
