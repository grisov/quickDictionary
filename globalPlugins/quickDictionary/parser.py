import os
import re

def get_attrs(resp):
    attrs = []
    for key in ["pos", "asp", "num", "gen"]:
        if key in resp:
            field = {
                'num': _('<i>number</i>: '),
                'gen': _('<i>gender</i>: ')
                }.get(key, '') + resp[key]
            attrs.append(field)
    if attrs:
        return " (%s)" % ', '.join(attrs)
    return ''

def to_html(resp):
    if not isinstance(resp, dict):
        return '<h1>%s</h1>' % _('Parsing error!')
    code = list(resp)[0]
    if str(code).isdigit():
        return '<h1>%s: %d</h1>' % (resp[code], code)
    html = '<link rel="stylesheet" type="text/css" href="%s">\n' % os.path.join(os.path.dirname(__file__), 'style.css')
    for key in ['def', 'tr', 'mean', 'syn', 'ex']:
        if key in resp:
            html += {
                'mean': _('<p><i>Mean</i>: '),
                'syn': _('<p><i>Synonyms</i>:\n'),
                'ex': _('<p><i>Examples</i>:\n')
                }.get(key, '')
            if key == 'def':
                if not resp['def']:
                    html += '<h1>%s</h1>' % _('No results')
                for elem in resp['def']:
                    html += '<h1>' + elem['text'] + get_attrs(elem) + '</h1>\n'
                    html += to_html(elem)
                    html += '\n'
            if key == 'tr':
                html += '<ul>\n'
                for elem in resp['tr']:
                    html += '<li><b>' + elem['text'] + '</b>' + get_attrs(elem) + '\n'
                    html += to_html(elem)
                    html += '</li>\n';
                html += '</ul>\n'
            if key == 'mean':
                means = []
                for elem in resp['mean']:
                    means.append(elem['text'] + get_attrs(elem) )
                html += ', '.join(means) + '</p>\n'
                del(means)
                html += to_html(elem)
            if key == 'syn':
                syns = []
                for elem in resp['syn']:
                    syns.append(elem['text'] + get_attrs(elem))
                html += ', '.join(syns) + '</p>\n'
                del(syns)
                html += to_html(elem)
            if key == 'ex':
                exs = []
                for elem in resp['ex']:
                    tmp = elem['text'] + get_attrs(elem)
                    if 'tr' in elem:
                        trs = []
                        for extr in elem['tr']:
                            trs.append(extr['text'] + get_attrs(extr))
                        tmp += ' - ' + ', '.join(trs)
                        del(trs)
                    exs.append(tmp)
                html += ',\n'.join(exs) + '</p>'
                del(exs)
    return html

def to_text(resp):
    li = u"\u2022 "
    h1 = "# "
    text = to_html(resp).replace('<li>', li).replace('<h1>', h1)
    text = re.sub(r'\<[^>]*\>', '', text)
    text = '\r\n'.join((s for s in text.split('\n') if s))
    return text if text else str(resp)
