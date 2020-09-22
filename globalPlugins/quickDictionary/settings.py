#settings.py
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
        helpLabel = wx.StaticText(self, label=_("Select dictionary source and target language:"))
        helpLabel.Wrap(self.GetSize()[0])
        sizer.Add(helpLabel)
        fromSizer = wx.BoxSizer(wx.HORIZONTAL)
        # Translators: A setting in addon settings dialog.
        fromLabel = wx.StaticText(self, label=_("Source language:"))
        fromSizer.Add(fromLabel)
        self._fromChoice = wx.Choice(self, choices=[])
        fromSizer.Add(self._fromChoice)
        intoSizer = wx.BoxSizer(wx.HORIZONTAL)
        # Translators: A setting in addon settings dialog.
        intoLabel = wx.StaticText(self, label=_("Target language:"))
        intoSizer.Add(intoLabel)
        self._intoChoice = wx.Choice(self, choices=[])
        intoSizer.Add(self._intoChoice)
        self.widgetMaker(self._fromChoice, sorted(langs.fromList(), key=lambda l: l.name.lower()))
        self._fromChoice.Bind(wx.EVT_CHOICE, self.onSelectFrom)
        self.widgetMaker(self._intoChoice, langs.intoList(config.conf[_addonName]['from']))
        sizer.Add(fromSizer)
        sizer.Add(intoSizer)
        langFrom = self._fromChoice.FindString(langs[config.conf[_addonName]['from']].name)
        langTo = self._intoChoice.FindString(langs[config.conf[_addonName]['into']].name)
        self._fromChoice.Select(langFrom)
        self._intoChoice.Select(langTo)
        # Translators: A setting in addon settings dialog.
        self._copyToClipboardChk = wx.CheckBox(self, label=_("Copy translation result to clipboard"))
        self._copyToClipboardChk.SetValue(config.conf[_addonName]['copytoclip'])
        sizer.Add(self._copyToClipboardChk)
        # Translators: A setting in addon settings dialog.
        self._autoSwapChk = wx.CheckBox(self, label=_("Auto-swap languages"))
        self._autoSwapChk.SetValue(config.conf[_addonName]['autoswap'])
        sizer.Add(self._autoSwapChk)
        # Translators: A setting in addon settings dialog.
        self._useMirrorChk = wx.CheckBox(self, label=_("Use alternative server"))
        self._useMirrorChk.SetValue(config.conf[_addonName]['mirror'])
        sizer.Add(self._useMirrorChk)
        tokenSizer = wx.BoxSizer(wx.VERTICAL)
        # Translators: A setting in addon settings dialog.
        tokenLabel = wx.StaticText(self, label=_("Dictionary Access Token:"))
        tokenSizer.Add(tokenLabel)
        self._tokenInput = wx.TextCtrl(self, style=wx.TE_LEFT)
        tokenSizer.Add(self._tokenInput)
        url = 'https://yandex.com/dev/dictionary/keys/get/'
        # Translators: A setting in addon settings dialog.
        self._linkHref = wx.adv.HyperlinkCtrl(self, -1, label=_("Register your own access token"), url=url, style=wx.adv.HL_CONTEXTMENU | wx.adv.HL_DEFAULT_STYLE | wx.adv.HL_ALIGN_RIGHT)
        self._linkHref.Update()
        self._tokenInput.SetValue(config.conf[_addonName]['token'])
        tokenSizer.Add(self._linkHref)
        sizer.Add(tokenSizer)
        if self._tokenInput.GetValue() != TOKEN:
            tokenSizer.Hide(self._linkHref)

    def widgetMaker(self, widget, languages):
        """Creating a widget based on the sequence of Language classes to display it in a wx.Choice object.
        @param widget: widget based on a sequence of Language classes
        @type widget: list
        @param languages: list of languages available in the dictionary
        @type languages: generator of Language objects
        """
        for lang in languages:
            widget.Append(lang.name, lang)

    def onSelectFrom(self, event):
        """Filling in the list of available destination languages when selecting the source language.
        @param event: event indicating the selection of an item in the wx.Choice object
        @type event: wx.core.PyEventBinder
        """
        fromLang = self._fromChoice.GetClientData(self._fromChoice.GetSelection()).code
        self._intoChoice.Clear()
        self.widgetMaker(self._intoChoice, sorted(langs.intoList(fromLang), key=lambda l: l.name.lower()))

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
        accessToken = self._tokenInput.GetValue()
        config.conf[_addonName]['token'] = accessToken if accessToken else TOKEN
