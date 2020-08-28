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
import api, ui
from threading import Thread
from .translator import Translation
from .shared import copyToClipboard, getSelectedText, langName

LANG1, LANG2 = 'en', 'ru'
TOKEN = ''


class GlobalPlugin(globalPluginHandler.GlobalPlugin):
    scriptCategory = str(_addonSummary)

    @script(description=_("Announces the translation of the current selected word or phrase, press twice to copy to clipboard"))
    def script_translateAnnounce(self, gesture):
        text = getSelectedText()
        translation = Translation(text, '%s-%s' % (LANG1, LANG2))
        text = '%s-%s\r\n%s' % (langName(LANG1), langName(LANG2), translation.text)
        if getLastScriptRepeatCount() == 0:
            Thread(target=ui.message, args=[text]).start()
        elif getLastScriptRepeatCount() >= 1:
            shared.copyToClipboard(text)

    @script(description=_("Displays translation results in a window, press twice to copy to clipboard"))
    def script_translateBox(self, gesture):
        text = getSelectedText()
        translation = Translation(text, '%s-%s' % (LANG1, LANG2))
        Thread(target=ui.browseableMessage, args=[translation.html, '%s (%s-%s)' % (text, langName(LANG1), langName(LANG2)), True]).start()
        if getLastScriptRepeatCount() == 0:
            pass
        elif getLastScriptRepeatCount() >= 1:
            shared.copyToClipboard(text)

    @script(description=_("Change the order of the selected languages for translation, press twice to select other languages"))
    def script_swapLanguages(self, gesture):
        if getLastScriptRepeatCount() == 0:
            ui.message('%s-%s' % (langName(LANG2), langName(LANG1)))
        elif getLastScriptRepeatCount() >= 1:
            ui.message('Select languages from list')

    __gestures = {
        "kb:NVDA+w": "translateAnnounce",
        "kb:NVDA+shift+w": "translateBox",
        "kb:NVDA+control+w": "swapLanguages"
    }
