#__init__.py
# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.
# See the file COPYING for more details.
# Copyright (C) 2020 Olexandr Gryshchenko <grisov.dev@mailnull.com>

import addonHandler
addonHandler.initTranslation()

import os
_addonDir = os.path.join(os.path.dirname(__file__), "..", "..")
if isinstance(_addonDir, bytes):
    _addonDir = _addonDir.decode("mbcs")
_curAddon = addonHandler.Addon(_addonDir)
_addonName = _curAddon.manifest['name']
_addonSummary = _curAddon.manifest['summary']

import globalPluginHandler
from scriptHandler import script, getLastScriptRepeatCount
import api, ui, config
import gui, wx
from time import sleep
from tones import beep
from threading import Thread
from .dictionary import Translator
from .shared import copyToClipboard, getSelectedText, finally_
from .languages import langs
from .settings import QuickDictionarySettingsPanel, TOKEN


class GlobalPlugin(globalPluginHandler.GlobalPlugin):
    scriptCategory = str(_addonSummary)

    def __init__(self, *args, **kwargs):
        super(GlobalPlugin, self).__init__(*args, **kwargs)
        confspec = {
            "from": "string(default=%s)" % langs.defaultFrom,
            "into": "string(default=%s)" % langs.defaultInto,
            "autoswap": "boolean(default=true)",
            "copytoclip": "boolean(default=true)",
            "token": "string(default=%s)" % TOKEN,
            "mirror": "boolean(default=false)"
        }
        config.conf.spec[_addonName] = confspec
        gui.settingsDialogs.NVDASettingsDialog.categoryClasses.append(QuickDictionarySettingsPanel)
        self._toggleGestures = False

    @property
    def source(self):
        return config.conf[_addonName]['from']

    @source.setter
    def source(self, lang):
        config.conf[_addonName]['from'] = lang

    @property
    def target(self):
        return config.conf[_addonName]['into']

    @target.setter
    def target(self, lang):
        config.conf[_addonName]['into'] = lang

    @property
    def isCopyToClipboard(self):
        return config.conf[_addonName]['copytoclip']

    @property
    def isAutoSwap(self):
        return config.conf[_addonName]['autoswap']

    def terminate(self):
        try:
            gui.settingsDialogs.NVDASettingsDialog.categoryClasses.remove(QuickDictionarySettingsPanel)
        except IndexError:
            pass

    def getScript(self, gesture):
        if not self._toggleGestures:
            return globalPluginHandler.GlobalPlugin.getScript(self, gesture)
        script = globalPluginHandler.GlobalPlugin.getScript(self, gesture)
        if not script:
            script = finally_(self.script_error, self.finish)
        return finally_(script, self.finish)

    def finish(self):
        self._toggleGestures = False
        self.clearGestureBindings()
        self.bindGestures(self.__gestures)

    def script_error(self, gesture):
        beep(150, 100)

    def script_addonLayer(self, gesture):
        # A run-time binding will occur from which we can perform various layered translation commands.
        # First, check if a second press of the script was done.
        if self._toggleGestures:
            self.script_error(gesture)
            return
        self.bindGestures(self.__addonGestures)
        self._toggleGestures = True
        beep(100, 10)

    @script(description=_("Announces the translation of the current selected word or phrase [D] or [NVDA+D]"))
    def script_dictionaryAnnounce(self, gesture):
        text = getSelectedText()
        if not text: return
        Thread(target=self.translate, args=[text, False, False]).start()

    @script(description=_("Displays dictionary results in a separate window [W]"))
    def script_dictionaryBox(self, gesture):
        text = getSelectedText()
        if not text: return
        Thread(target=self.translate, args=[text, True, False]).start()

    @script(description=_("It announces the current source and target languages [A]"))
    def script_announceLanguages(self, gesture):
        # Translators: message presented to announce the current source and target languages.
        ui.message(_("Translate: from {lang1} to {lang2}").format(lang1=langs[self.source].name, lang2=langs[self.target].name))

    @script(description=_("Change the order of the selected languages for translation [S]"))
    def script_swapLanguages(self, gesture):
        if langs.isAvailable(self.target, self.source):
            self.source, self.target = self.target, self.source
            ui.message(_("Languages swapped"))
            ui.message('%s - %s' % (self.source, self.target))
            text = getSelectedText()
            if not text: return
            Thread(target=self.translate, args=[text, False, False]).start()
        else:
            ui.message(_('Swap languages is not available for this pair') + ': %s - %s' % (langs[self.source].name, langs[self.target].name))

    @script(description=_("Copy last dictionary result to the clipboard [C]"))
    def script_copyLastResult(self, gesture):
        pass

    @script(description=_("Announce help message [H]"))
    def script_announceHelp(self, gesture):
        ui.message(_("D or NVDA+D - translates selected/clipboard word or phrase, W - displays dictionary results in a separate window, A - announces current source and target languages, S - swaps source and target languages, C - copies last result to clipboard, O - open dictionary settings dialog, H - displays this message."))

    @script(description=_("Displays the add-on settings window [O]"))
    def script_showSettings(self, gesture):
        wx.CallAfter(gui.mainFrame._popupSettingsDialog, gui.settingsDialogs.NVDASettingsDialog, QuickDictionarySettingsPanel)

    def translate(self, text, isHtml=False, copyToClip=False):
        pairs = [(self.source, self.target)]
        if self.isAutoSwap:
            pairs.append((self.target, self.source))
        for lFrom, lInto in pairs:
            translator = Translator(lFrom, lInto, text)
            translator.start()
            i=0
            while translator.is_alive():
                sleep(0.1)
                if i == 10:
                    beep(500, 100)
                    i = 0
                i+=1
            translator.join()
            if translator.plaintext:
                break
        else:
            if not translator.plaintext:
                ui.message(_('No results'))
                return
        if isHtml:
            ui.browseableMessage(translator.html, title='%s-%s' % (langs[translator.langFrom].name, langs[translator.langTo].name), isHtml=isHtml)
        else:
            ui.message('%s-%s' % (langs[translator.langFrom].name, langs[translator.langTo].name))
            ui.message(translator.plaintext)
        if copyToClip or self.isCopyToClipboard:
            copyToClipboard(translator.plaintext)

    __addonGestures = {
        "kb:NVDA+d": "dictionaryAnnounce",
        "kb:d": "dictionaryAnnounce",
        "kb:w": "dictionaryBox",
        "kb:a": "announceLanguages",
        "kb:s": "swapLanguages",
        "kb:c": "copyLastResult",
        "kb:o": "showSettings",
        "kb:h": "announceHelp",
    }

    __gestures = {
        "kb:NVDA+d": "addonLayer",
        "kb:NVDA+alt+d": "swapLanguages",
        "kb:NVDA+windows+d": "showSettings"
    }
