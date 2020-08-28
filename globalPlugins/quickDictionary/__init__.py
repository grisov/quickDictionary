#-*- coding:utf-8 -*-
# Copyright (C) 2020 Olexandr Gryshchenko <grisov.dev@mailnull.com>
#This file is covered by the GNU General Public License.
#See the file COPYING for more details.

import addonHandler
import os
_addonDir = os.path.join(os.path.dirname(__file__), "..", "..")
if isinstance(_addonDir, bytes):
    _addonDir = _addonDir.decode("mbcs")
_curAddon = addonHandler.Addon(_addonDir)
_addonSummary = _curAddon.manifest['summary']
addonHandler.initTranslation()

import globalPluginHandler
from scriptHandler import script, getLastScriptRepeatCount
import api, ui, config
from threading import Thread
from .translator import Translation
from .shared import copyToClipboard, getSelectedText, langName

config.conf['quickdictionary'] = {
    'from': 'en',
    'into': 'ru',
    'token': 'dict.1.1.20160512T220906Z.4a4ee160a921aa01.a74981e0761f48a1309d4f903e540f1f3288f1a3'}


class GlobalPlugin(globalPluginHandler.GlobalPlugin):
    scriptCategory = str(_addonSummary)

    def __init__(self, *args, **kwargs):
        super(GlobalPlugin, self).__init__(*args, **kwargs)

    @property
    def source(self):
        return config.conf['quickdictionary']['from']

    @source.setter
    def source(self, lang):
        config.conf['quickdictionary']['from'] = lang

    @property
    def target(self):
        return config.conf['quickdictionary']['into']

    @target.setter
    def target(self, lang):
        config.conf['quickdictionary']['into'] = lang

    @script(description=_("Announces the translation of the current selected word or phrase, press twice to copy to clipboard"))
    def script_translateAnnounce(self, gesture):
        text = getSelectedText()
        translation = Translation(text, '%s-%s' % (self.source, self.target))
        text = '%s-%s\r\n%s' % (langName(self.source), langName(self.target), translation.text)
        if getLastScriptRepeatCount() == 0:
            Thread(target=ui.message, args=[text]).start()
        elif getLastScriptRepeatCount() >= 1:
            shared.copyToClipboard(text)

    @script(description=_("Displays translation results in a window, press twice to copy to clipboard"))
    def script_translateBox(self, gesture):
        text = getSelectedText()
        translation = Translation(text, '%s-%s' % (self.source, self.target))
        Thread(target=ui.browseableMessage, args=[translation.html, '%s (%s-%s)' % (text, langName(self.source), langName(self.target)), True]).start()
        if getLastScriptRepeatCount() == 0:
            pass
        elif getLastScriptRepeatCount() >= 1:
            shared.copyToClipboard(text)

    @script(description=_("Change the order of the selected languages for translation, press twice to select other languages"))
    def script_swapLanguages(self, gesture):
        if getLastScriptRepeatCount() == 0:
            self.source, self.target = self.target, self.source
            ui.message('%s-%s' % (langName(self.source), langName(self.target)))
        elif getLastScriptRepeatCount() >= 1:
            ui.message('Select languages from list')

    __gestures = {
        "kb:NVDA+w": "translateAnnounce",
        "kb:NVDA+shift+w": "translateBox",
        "kb:NVDA+control+w": "swapLanguages"
    }
