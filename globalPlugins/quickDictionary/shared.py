import api
import ui
from textInfos import POSITION_SELECTION
from languageHandler import getLanguageDescription
from tones import beep

def copyToClipboard(object):
    if api.copyToClip(object):
        ui.message(_("Copied to clipboard."))
    else:
        ui.message(_("Copy faildd."))

def getSelectedText():
    obj = api.getFocusObject()
    treeInterceptor = obj.treeInterceptor
    if hasattr(treeInterceptor, 'TextInfo') and not treeInterceptor.passThrough:
        obj = treeInterceptor
    try:
        info = obj.makeTextInfo(POSITION_SELECTION)
    except:
        info = None
    if not info or info.isCollapsed or info.text.isspace():
        # user has pressed the shortcut key for translating selected text, but no text was actually selected.
        try:
            text = api.getClipData()
        except:
            ui.message(_("There is no text on the clipboard"))
            text = None
        if text and isinstance(text, str) and not text.isspace():
            return text
        ui.message("There is no selected text")
        beep(150, 100)
        return ''
    return info.text

def langName(code):
    return getLanguageDescription(code)
