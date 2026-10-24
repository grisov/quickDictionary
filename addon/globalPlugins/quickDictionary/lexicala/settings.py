# settings.py
# Contains a description of the settings panel of a specific service
# A part of the NVDA Quick Dictionary add-on
# This file is covered by the GNU General Public License.
# See the file COPYING for more details.
# Copyright (C) 2020-2026 Olexandr Gryshchenko <grisov.nvaccess@mailnull.com>

from collections.abc import Callable, Iterator

import addonHandler
import wx
from gui import guiHelper
from logHandler import log

from ..configuration import getAddonConfig
from ..service import secrets
from .api import serviceName
from .languages import ServiceLanguage, langs

try:
	addonHandler.initTranslation()
except addonHandler.AddonError:
	log.warning("Unable to init translations. This may be because the addon is running from NVDA scratchpad.")
_: Callable[[str], str]


class ServicePanel(wx.Panel):
	"""The Settings Panel that specific to the current service."""

	def __init__(
		self,
		parent: wx.Window | None = None,
		id: int = wx.ID_ANY,
	) -> None:
		"""Create a settings panel for a specific service.
		Populate the service panel with settings controls.
		@param parent:
		@type parent: wx.Window | None
		@param id:
		@type id: int
		"""
		super(ServicePanel, self).__init__(parent, id)
		addonHelper = guiHelper.BoxSizerHelper(self, orientation=wx.VERTICAL)
		self.SetSizer(addonHelper.sizer)
		self.sourceChoice = addonHelper.addLabeledControl(
			# Translators: A setting in addon settings dialog.
			_("&Dictionary:"),
			wx.Choice,
			choices=langs.sources,
			style=wx.CB_SORT,
		)
		currentSource: int = self.sourceChoice.FindString(getAddonConfig()[serviceName]["source"])
		self.sourceChoice.Select(currentSource)
		self.sourceChoice.Bind(wx.EVT_CHOICE, self.onSelectSource)
		addonHelper.addItem(
			# Translators: Help message for a dialog.
			wx.StaticText(
				self,
				label=_("Select dictionary source and target language:"),
				style=wx.ALIGN_LEFT,
			),
		)
		languageHelper = guiHelper.BoxSizerHelper(self, orientation=wx.HORIZONTAL)
		self.fromChoice = languageHelper.addLabeledControl(
			# Translators: A setting in addon settings dialog.
			_("&Source language:"),
			wx.Choice,
			choices=[],
			style=wx.CB_SORT,
		)
		self.intoChoice = languageHelper.addLabeledControl(
			# Translators: A setting in addon settings dialog.
			_("&Target language:"),
			wx.Choice,
			choices=[],
			style=wx.CB_SORT,
		)
		addonHelper.addItem(languageHelper)
		self.widgetMaker(
			self.fromChoice,
			langs.fromList(source=getAddonConfig()[serviceName]["source"]),
		)
		self.widgetMaker(
			self.intoChoice,
			langs.intoList(source=getAddonConfig()[serviceName]["source"]),
		)
		langFrom: int = self.fromChoice.FindString(langs[getAddonConfig()[serviceName]["from"]].name)
		langTo: int = self.intoChoice.FindString(langs[getAddonConfig()[serviceName]["into"]].name)
		self.fromChoice.Select(langFrom)
		self.intoChoice.Select(langTo)

		self.morphChk = addonHelper.addItem(
			# Translators: A setting in addon settings dialog.
			wx.CheckBox(self, label=_("Search in both headwords and &inflections")),
		)
		self.morphChk.SetValue(getAddonConfig()[serviceName]["morph"])
		self.analyzedChk = addonHelper.addItem(
			# Translators: A setting in addon settings dialog.
			wx.CheckBox(self, label=_("St&rip words to their stem")),
		)
		self.analyzedChk.SetValue(getAddonConfig()[serviceName]["analyzed"])
		self.allChk = addonHelper.addItem(
			# Translators: A setting in addon settings dialog.
			wx.CheckBox(self, label=_("Show a&ll available translations")),
		)
		self.allChk.SetValue(getAddonConfig()[serviceName]["all"])
		self.copyToClipboardChk = addonHelper.addItem(
			# Translators: A setting in addon settings dialog.
			wx.CheckBox(self, label=_("Copy dictionary response to clip&board")),
		)
		self.copyToClipboardChk.SetValue(getAddonConfig()[serviceName]["copytoclip"])
		self.autoSwapChk = addonHelper.addItem(
			# Translators: A setting in addon settings dialog.
			wx.CheckBox(self, label=_("Auto-s&wap languages")),
		)
		self.autoSwapChk.SetValue(getAddonConfig()[serviceName]["autoswap"])

		# Fields for input user credentials and link to registration
		secret = secrets[serviceName]
		authHelper = guiHelper.BoxSizerHelper(self, orientation=wx.HORIZONTAL)
		self.usernameInput = authHelper.addLabeledControl(
			# Translators: A setting in addon settings dialog.
			_("&Username:"),
			wx.TextCtrl,
			value=secret.decode(getAddonConfig()[serviceName]["username"]),
			style=wx.TE_LEFT,
		)
		self.passwordInput = authHelper.addLabeledControl(
			# Translators: A setting in addon settings dialog.
			_("&Password:"),
			wx.TextCtrl,
			value=secret.decode(getAddonConfig()[serviceName]["password"]),
			style=wx.TE_LEFT | wx.TE_PASSWORD,
		)
		addonHelper.addItem(authHelper)

		self.linkHref = addonHelper.addItem(
			wx.adv.HyperlinkCtrl(
				self,
				id=wx.ID_ANY,
				# Translators: A hyperlink in addon settings dialog.
				label=_("Register your own access token"),
				url=secret.url,
				style=wx.adv.HL_CONTEXTMENU | wx.adv.HL_DEFAULT_STYLE | wx.adv.HL_ALIGN_RIGHT,
			),
		)
		self.linkHref.Update()
		self.linkHref.Show(
			show=self.usernameInput.GetValue() == secret.username
			and self.passwordInput.GetValue() == secret.password,
		)
		addonHelper.sizer.Fit(self)

	def onSelectSource(self, event: wx.PyEvent) -> None:
		"""Fill in the lists of source and target languages when selecting source dictionary.
		@param event: event indicating the selection of an item in the wx.Choice object
		@type event: wx.PyEvent
		"""
		source: str = event.GetString()
		self.fromChoice.Clear()
		self.widgetMaker(self.fromChoice, langs.fromList(source=source))
		self.intoChoice.Clear()
		self.widgetMaker(self.intoChoice, langs.intoList(source=source))
		langFrom: int = self.fromChoice.FindString(langs[getAddonConfig()[serviceName]["from"]].name)
		langTo: int = self.intoChoice.FindString(langs[getAddonConfig()[serviceName]["into"]].name)
		langFrom = max(0, langFrom)
		langTo = max(0, langTo)
		self.fromChoice.Select(langFrom)
		self.intoChoice.Select(langTo)

	def widgetMaker(self, widget: wx.Choice, languages: Iterator[ServiceLanguage]) -> None:
		"""Creating a widget based on the sequence of Language classes to display it in a wx.Choice object.
		@param widget: widget based on a sequence of Language classes
		@type widget: wx.Choice
		@param languages: list of languages available in the dictionary
		@type languages: Iterator[ServiceLanguage]
		"""
		for lang in languages:
			widget.Append(lang.name, lang)

	def save(self) -> None:
		"""Save the state of the service panel settings."""
		getAddonConfig()[serviceName]["source"] = self.sourceChoice.GetString(
			self.sourceChoice.GetSelection(),
		)
		fromLang: str = self.fromChoice.GetClientData(self.fromChoice.GetSelection()).code
		intoLang: str = self.intoChoice.GetClientData(self.intoChoice.GetSelection()).code
		getAddonConfig()[serviceName]["from"] = fromLang
		getAddonConfig()[serviceName]["into"] = intoLang
		getAddonConfig()[serviceName]["morph"] = self.morphChk.GetValue()
		getAddonConfig()[serviceName]["analyzed"] = self.analyzedChk.GetValue()
		getAddonConfig()[serviceName]["all"] = self.allChk.GetValue()
		getAddonConfig()[serviceName]["copytoclip"] = self.copyToClipboardChk.GetValue()
		getAddonConfig()[serviceName]["autoswap"] = self.autoSwapChk.GetValue()
		getAddonConfig()[serviceName]["username"] = secrets[serviceName].encode(
			self.usernameInput.GetValue() or secrets[serviceName].username,
		)
		getAddonConfig()[serviceName]["password"] = secrets[serviceName].encode(
			self.passwordInput.GetValue() or secrets[serviceName].password,
		)
