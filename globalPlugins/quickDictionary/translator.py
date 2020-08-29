# encoding: utf-8
import ssl
import threading
from urllib.request import Request, urlopen
from json import dumps, loads
import config
from .parser import Parser

ssl._create_default_https_context = ssl._create_unverified_context


class Translator(threading.Thread):

    def __init__(self, langFrom, langTo, text, uiLang, isHtml=False, *args, **kwargs):
        super(Translator, self).__init__(*args, **kwargs)
        self._stopEvent = threading.Event()
        self._langFrom = langFrom
        self._langTo = langTo
        self._text = text
        self._uiLang = uiLang
        self._isHtml = isHtml
        self._translation = ''

    langFrom = lambda self: self._langFrom
    langTo = lambda self: self._langTo
    text = lambda self: self._text
    uiLang = lambda self: self._uiLang
    isHtml = lambda self: self._isHtml
    translation = lambda self: self._translation

    langFrom = property(langFrom)
    langTo = property(langTo)
    text = property(text)
    uiLang = property(uiLang)
    isHtml = property(isHtml)
    translation = property(translation)

    def stop(self):
        self._stopEvent.set()

    def run(self):
        data = {
            'text': self.text,
            'lang': '%s-%s' % (self.langFrom, self.langTo)}
        if config.conf['quickdictionary']['token']:
            data['key'] = config.conf['quickdictionary']['token']
        data = bytes(str(dumps(data)), encoding='utf-8')
        headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla 5.0'}
        url = 'https://info.alwaysdata.net/v1/proxy'
        rq = Request(url, data=data, method='POST', headers=headers)
        try:
            resp = urlopen(rq)
        except Exception as e:
            self._translation = 'Error: ' + str(e)
            return
        text = loads(resp.read().decode())['answer']
        if isinstance(text, str):
            text = loads(text)
        parser = Parser(text)
        self._translation = parser.to_html() if self.isHtml else parser.to_text()
