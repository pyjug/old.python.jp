# -*- coding: utf-8 -*-

import yaml, glob, os, sys, sha, PyRSS2Gen
from datetime import tzinfo, timedelta, datetime

def find_files(d):
    files = glob.glob(os.path.join(d, '*'))
    ret = [f for f in files if os.path.isfile(f)]
    ret = [f for f in files if not f.startswith('.')]
    return ret

class UTC(tzinfo):
    """UTC"""

    def utcoffset(self, dt):
        return timedelta(0)

    def tzname(self, dt):
        return "UTC"

    def dst(self, dt):
        return timedelta(0)

class JST(tzinfo):

    def __init__(self):
        self.__offset = timedelta(hours=9)
        self.__name = 'JST'

    def utcoffset(self, dt):
        return self.__offset

    def tzname(self, dt):
        return self.__name

    def dst(self, dt):
        return timedelta(0)

def read_yaml(f):
    d = yaml.load(open(f).read())
    d['filename'] = os.path.split(f)[1]
    d['hash'] = sha.sha(d['filename']).hexdigest()
    if d['type'] == 'news':
        path = '/news/#'
    else:
        path = '/community/%s/#' % d['type']

    d['path'] = path+d['hash']

    ret = {}
    for k, v in d.items():
        if isinstance(v, datetime):
            v = v.replace(tzinfo=JST()).astimezone(UTC())
        ret[k] = v
    return ret

def read_files(d):
    files = find_files(d)
    data = [read_yaml(f) for f in files]
    return sorted(data, key=lambda d:d['date'], reverse=True)

def build_news(data):
    data = [d for d in data if d['type'] == 'news'][:40]

    header = u'''Content-type: text/x-rst
Title: Python News

Python ニュース
-------------------------


Python関連のニュース・告知など、このページに載せても良いという情報がありましたら `サイト運営まで </community/pyjug>`_ ご連絡ください。

'''

    temp = u'''

.. _%s:


%s
================================================================

*%s*

%s

'''
    all = []
    for d in data:
        s = temp % (d['hash'], d['title'], d['date'].strftime('%Y-%m-%d %H:%M'), d['text'], )
        all.append(s)

    return header + u'\n'.join(all)

def save_news(news):
    with open('data/news/content.ht', 'w') as f:
        f.write(news.encode('utf-8'))


def build_events(data):
    data = [d for d in data if d['type'] == 'event'][:40]

    header = u'''Content-type: text/x-rst
Title: Python イベント

Python 関連イベント
-------------------------

Python関連のコミュニティ・ユーザ会・企業のイベントや勉強会など、このページに載せても良いという情報がありましたら `サイト運営まで </community/pyjug>`_ ご連絡ください。

'''

    temp = u'''

.. _%s:


`%s <%s>`_
========================================================================================================

\ 

:日付: %s
:場所: %s

%s

%s

:掲載日: %s

'''

    data = sorted(data, key=lambda d:d['date'])
    all = []
    for d in data:
        if 'event-date-to' in d and d['event-date'].date() != d['event-date-to'].date():
            dt = d['event-date'].astimezone(JST())
            dt2 = d['event-date-to'].astimezone(JST())
            datestr = u' 〜 '.join([
                dt.strftime('%Y-%m-%d'),
                dt2.strftime('%Y-%m-%d')])
        else:
            datestr = d['event-date'].astimezone(JST()).strftime('%Y-%m-%d %H:%M')

        s = temp % (sha.sha(d['filename']).hexdigest(), 
            d['title'], d['link'], datestr, 
            d['location'], d['text'], d['description'],
            d['date'].astimezone(JST()).strftime('%Y-%m-%d %H:%M'), )
        all.append(s)

    return header + u'\n'.join(all)

def save_events(news):
    with open('data/community/event/content.ht', 'w') as f:
        f.write(news.encode('utf-8'))



def run(d):
    yamls = read_files(d)
    news = build_news(yamls)
    save_news(news)

    events = build_events(yamls)
    save_events(events)


if __name__ == '__main__':
    run('jp_data')
