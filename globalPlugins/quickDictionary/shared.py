#shared.py
import addonHandler
addonHandler.initTranslation()

import re
import api
import ui
from textInfos import POSITION_SELECTION
from tones import beep
from functools import wraps

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
    except (RuntimeError, NotImplementedError):
        info = None
    if not info or info.isCollapsed or not clearText(info.text):
        try:
            text = api.getClipData()
        except:
            text = ''
        if not text or not isinstance(text, str) or not clearText(text):
            # Translators: user has pressed the shortcut key for translating selected text, but no text was actually selected and clipboard is clear
            ui.message(_("There is no selected text, the clipboard is also empty, or its content is not text!"))
            return ''
        return clearText(text)
    return clearText(info.text)

def clearText(text):
    text = ''.join([s for s in text.strip() if s.isalpha() or s.isspace()])
    return ' '.join(re.split('\s+', text))

# Below toggle code came from Tyler Spivey's code, with enhancements by Joseph Lee.
def finally_(func, final):
    """Calls final after func, even if it fails."""
    def wrap(f):
        @wraps(f)
        def new(*args, **kwargs):
            try:
                func(*args, **kwargs)
            finally:
                final()
        return new
    return wrap(final)
