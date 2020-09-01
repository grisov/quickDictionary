#settings.py
import addonHandler
addonHandler.initTranslation()

import gui
import wx
import config
from . import _addonSummary
from .languages import langs


class QuickDictionarySettingsPanel(gui.SettingsPanel):
    # Translators: name of the settings dialog.
    title = _addonSummary

    def __init__(self, parent):
        super(QuickDictionarySettingsPanel, self).__init__(parent)

    def makeSettings(self, sizer):
        # Translators: Help message for a dialog.
        helpLabel = wx.StaticText(self, label=_("Select translation source and target language:"))
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
        self.widgetMaker(self._fromChoice, sorted(langs.fromList(), key=lambda l: l.name))
        self._fromChoice.Bind(wx.EVT_CHOICE, self.onSelectFrom)
        self.widgetMaker(self._intoChoice, langs.intoList(config.conf['quickdictionary']['from']))
        sizer.Add(fromSizer)
        sizer.Add(intoSizer)
        langFrom = self._fromChoice.FindString(langs[config.conf['quickdictionary']['from']].name)
        langTo = self._intoChoice.FindString(langs[config.conf['quickdictionary']['into']].name)
        self._fromChoice.Select(langFrom)
        self._intoChoice.Select(langTo)

    def widgetMaker(self, widget, languages):
        for lang in languages:
            widget.Append(lang.name, lang)

    def onSelectFrom(self, event):
        fromLang = self._fromChoice.GetClientData(self._fromChoice.GetSelection()).code
        self._intoChoice.Clear()
        self.widgetMaker(self._intoChoice, sorted(langs.intoList(fromLang), key=lambda l: l.name))

    def postInit(self):
        self._fromChoice.SetFocus()

    def onSave(self):
        fromLang = self._fromChoice.GetClientData(self._fromChoice.GetSelection()).code
        intoLang = self._intoChoice.GetClientData(self._intoChoice.GetSelection()).code
        config.conf['quickdictionary']['from'] = fromLang
        config.conf['quickdictionary']['into'] = intoLang
