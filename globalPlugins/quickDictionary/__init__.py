#-*- coding:utf-8 -*-
# Copyright (C) 2020 Olexandr Gryshchenko <grisov.dev@mailnull.com>
#This file is covered by the GNU General Public License.
#See the file COPYING for more details.

import addonHandler
import os
_addonDir = os.path.join(os.path.dirname(__file__), "..", "..")
addonHandler.initTranslation()

import globalPluginHandler
from scriptHandler import script
import api, ui

LANG1, LANG2 = 'en', 'ru'


class GlobalPlugin(globalPluginHandler.GlobalPlugin):

    @script()
    def script_translateAnnounce(self, gesture):
        pass

    @script()
    def script_translateBox(self, gesture):
        pass

    @script()
    def script_swapLanguages(self, gesture):
        pass

    __gestures = {
        "kb:NVDA+w": "translateAnnounce",
        "kb:NVDA+shift+w": "translateBox",
        "kb:NVDA+control+w": "swapLanguages"
    }
