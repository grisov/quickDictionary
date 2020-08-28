import ssl
import urllib.request as urllibRequest
import threading
from urllib.request import Request, urlopen
from json import dumps, loads
from .parser import to_html, to_text

ssl._create_default_https_context = ssl._create_unverified_context


class Translation(object):

    def __init__(self, word, lang='en-uk', token='', is_html=False):
        self._word = word
        self._lang = lang
        self._ui_lang = 'uk'
        self._token = token
        self._is_html = is_html
        self._response = {}

    @property
    def word(self):
        return self._word

    @word.setter
    def word(self, word):
        self._word = word

    @property
    def lang(self):
        return self._lang

    @lang.setter
    def lang(self, lang):
        self._lang = lang

    @property
    def token(self):
        return self._token

    @token.setter
    def token(self, token):
        self._token = token

    @property
    def is_html(self):
        return self._is_html

    @is_html.setter
    def is_html(self, is_html):
        self._is_html = is_html

    @property
    def html(self):
        if not self._response:
            self.get_translation()
        return to_html(self._response)

    @property
    def text(self):
        if not self._response:
            self.get_translation()
        return to_text(self._response)

    def __repr__(self):
        return self.text

    @property
    def request_data(self):
        data = {
            'text': self.word,
            'lang': self.lang
        }
        if self.token:
            data['key'] = self.token
        return data

    def get_translation(self):
        data = bytes(str(dumps(self.request_data)), encoding='utf-8')
        headers = {'Content-Type': 'application/json'}
        url = 'https://info.alwaysdata.net/v1/proxy'
        rq = Request(url, data=data, method='POST', headers=headers)
        try:
            resp = urlopen(rq)
        except:
            self._response = {502: 'Unable to connect to API Proxy server'}
            return self._response
        self._response = loads(resp.read().decode())['answer']
        if isinstance(self._response, str):
            self._response = loads(self._response)
        return self._response
