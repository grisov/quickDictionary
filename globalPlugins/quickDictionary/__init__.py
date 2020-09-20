#__init__.py
# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.
# See the file COPYING for more details.
# Copyright (C) 2020 Olexandr Gryshchenko <grisov.nvaccess@mailnull.com>

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
from scriptHandler import script
from queueHandler import queueFunction, eventQueue
import api, ui, config
import gui, wx
from tones import beep
from threading import Thread
from .shared import copyToClipboard, getSelectedText, translateWithCaching, messageWithLangDetection, finally_
from .languages import langs
from .settings import QuickDictionarySettingsPanel
from .secret import APIKEY as TOKEN


class GlobalPlugin(globalPluginHandler.GlobalPlugin):
    scriptCategory = str(_addonSummary)

    def __init__(self, *args, **kwargs):
        super(GlobalPlugin, self).__init__(*args, **kwargs)
        confspec = {
            "from": "string(default=%s)" % langs.defaultFrom,
            "into": "string(default=%s)" % langs.defaultInto,
            "autoswap": "boolean(default=false)",
            "copytoclip": "boolean(default=false)",
            "token": "string(default=%s)" % TOKEN,
            "mirror": "boolean(default=false)"
        }
        config.conf.spec[_addonName] = confspec
        gui.settingsDialogs.NVDASettingsDialog.categoryClasses.append(QuickDictionarySettingsPanel)
        self._toggleGestures = False
        self._lastTranslator = None

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
        beep(100, 100)

    def script_addonLayer(self, gesture):
        # A run-time binding will occur from which we can perform various layered translation commands.
        # First, check if a second press of the script was done.
        if self._toggleGestures:
            self.script_error(gesture)
            return
        self.bindGestures(self.__addonGestures)
        self._toggleGestures = True
        beep(200, 10)

    @script(description=_("Announces the translation of the current selected word or phrase [D] or [NVDA+D]"))
    def script_dictionaryAnnounce(self, gesture):
        text = getSelectedText()
        if not text: return
        Thread(target=self.translate, args=[text, False]).start()

    @script(description=_("Displays dictionary results in a separate window [W]"))
    def script_dictionaryBox(self, gesture):
        text = getSelectedText()
        if not text: return
        Thread(target=self.translate, args=[text, True]).start()

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
            Thread(target=self.translate, args=[text, False]).start()
        else:
            ui.message(_('Swap languages is not available for this pair') + ': %s - %s' % (langs[self.source].name, langs[self.target].name))

    @script(description=_("Copy last dictionary result to the clipboard [C]"))
    def script_copyLastResult(self, gesture):
        if not self._lastTranslator:
            ui.message(_("There is no dictionary queries"))
            return
        copyToClipboard(self._lastTranslator.plaintext)
        ui.message('%s-%s' % (langs[self._lastTranslator.langFrom].name, langs[self._lastTranslator.langTo].name))
        ui.message(self._lastTranslator.plaintext)

    @script(description=_("Announce help message [H]"))
    def script_announceHelp(self, gesture):
        for message in [
            _("NVDA + D - switch to add-on control mode,"),
            _("to get a quick translation of a word or phrase - press NVDA + D twice;"),
            _("NVDA + Alt + D - swap languages and get quick translation;"),
            _("NVDA + Windows + D - quick access to add-on settings."),
            "...",
            _("In add-on control mode:"),
            _("D - translation of a word or phrase (the same as NVDA+D twice);"),
            _("W - show translation in a separate browseable window;"),
            _("A - anounce the current pair of languages ??for translation;"),
            _("S - swap languages and get quick translation (same as NVDA + Alt + D);"),
            _("C - copy last translation result to the clipboard;"),
            _("O - open dictionary add-on settings dialog (same as NVDA + Windows + D);"),
            _("H - announce this help message.")]:
            ui.message(message)

    @script(description=_("Displays the add-on settings dialog [O]"))
    def script_showSettings(self, gesture):
        """Displays the add-on settings dialog"""
        wx.CallAfter(gui.mainFrame._popupSettingsDialog, gui.settingsDialogs.NVDASettingsDialog, QuickDictionarySettingsPanel)

    def translate(self, text, isHtml=False):
        pairs = [(self.source, self.target)]
        if self.isAutoSwap:
            pairs.append((self.target, self.source))
        for lFrom, lInto in pairs:
            translator = translateWithCaching(lFrom, lInto, text)
            if translator.plaintext:
                break
        else:
            if not translator.plaintext:
                ui.message(_('No results'))
                return
        self._lastTranslator = translator
        if isHtml:
            ui.browseableMessage(translator.html, title='%s-%s' % (langs[translator.langFrom].name, langs[translator.langTo].name), isHtml=isHtml)
        else:
            ui.message('%s-%s' % (langs[translator.langFrom].name, langs[translator.langTo].name))
            queueFunction(eventQueue, messageWithLangDetection,
                {'text': translator.plaintext, 'lang': translator.langTo})
        if self.isCopyToClipboard:
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
