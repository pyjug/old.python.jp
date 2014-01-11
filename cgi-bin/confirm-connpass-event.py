#!/usr/bin/env python
# -*- coding: utf-8
import cgitb
cgitb.enable()

import os, sys, cgi, re, json, urllib2, string, hashlib, os, time, subprocess
import datetime
import dateutil.parser
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.mime.application import MIMEApplication
from email.Header import Header
from email.encoders import encode_base64


JSON_DIR = '/var/www/connpass-reqs/'
SENDMAIL = '/usr/sbin/sendmail'

def check(reqid):
    if not re.match(r'[0-9a-hA-H]+', reqid):
        print('IDが正しくありません')
        return
    if not os.path.exists(os.path.join(JSON_DIR, reqid)):
        print('IDが正しくありません')
        return
    return True

def _to_utf8(s):
    if isinstance(s, unicode):
        return s.encode('utf-8')
    return s

def to_yaml(src):
    ev = src['events'][0]
    rec = {'type': 'event'}
    rec['req-mailaddr'] = _to_utf8(src['req-mailaddr']
    rec['title'] =  _to_utf8(ev['title'])
    rec['date'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S +09:00')
    d = dateutil.parser.parser(ev['started_at'])
    rec['event-date'] =  d.strftime('%Y-%m-%d %H:%M:%S +09:00')
    d = dateutil.parser.parser(ev['end_at'])
    rec['event-date-to'] =  d.strftime('%Y-%m-%d %H:%M:%S +09:00')
    rec['location'] =  _to_utf8(ev['address'])
    rec['link'] =  _to_utf8(ev['event_url'])
    rec['text'] =  _to_utf8(ev['catch'])
    rec['description'] =  _to_utf8(ev['description'])

    return unicode(yaml.safe_dump(
                        rec, default_style='|', allow_unicode=True,
                        encoding='utf-8'), 
                   'utf-8')

msg = u'''

Python.jpサイトへの、イベント告知掲載リクエストを受け取りました。

確認のため、以下のURLにアクセスしてリクエストを確定してください。

%s

%s

'''

def sendmail(reqid):
    mailaddr = 'ishimoto@gembook.org'
    with open(os.path.join(JSON_DIR, reqid), 'r') as f:
        s = f.read()
    mail = MIMEMultipart()
    mail['From'] = 'noreply@python.jp'
    mail['To'] = mailaddr
    mail['Subject'] = Header(u'Python.jp イベント登録の確認', 'utf-8')

    y = to_yaml(s)
    mail.attach(MIMEText(msg % (reqid, y), _charset='utf-8'))
    
    j = MIMEApplication(y.encode('utf-8'), 'octet-stream', encode_base64)
    j.add_header('Content-Disposition', 
                 'attachment; filename="%s.json"' % reqid)
    mail.attach(j)

    p = subprocess.Popen([SENDMAIL, mailaddr], stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    o, e =  p.communicate(mail.as_string())
    if p.returncode:
        print o, e, p.returncode
        return

    return True

def main():
    form = cgi.FieldStorage()

    print "Content-Type: text/html"
    print

    print '''<meta http-equiv="Content-type" content="text/html;charset=UTF-8">'''

    reqid = form.getfirst('reqid', '').strip()

    if not check(reqid):
        return

    if not sendmail(reqid):
        return

    print 'リクエストを確認しました。登録完了まで、しばらくお待ち下さい。'


main()
