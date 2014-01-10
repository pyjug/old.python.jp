#!/usr/bin/env python
# -*- coding: utf-8
import cgitb
cgitb.enable()

import sys, cgi, re, json, urllib2, string, hashlib, os, time, subprocess
from email.MIMEText import MIMEText
from email.Header import Header


JSON_DIR = '/var/www/connpass-reqs/'
VALID_CHARS = set("!#$%&'*+-/=?^_`{|}~.@"+string.ascii_letters+string.digits)
SENDMAIL = '/usr/sbin/sendmail'

def check(eventid, mailaddr):
    if not re.match(r'^\d+$', eventid):
        print('イベントIDが正しくありません')
        return

    mailaddr = mailaddr.strip()
    if not mailaddr or not set(mailaddr).issubset(VALID_CHARS):
        print ('メールアドレスが正しくありません')
        return
    return True

def search(eventid):
    response = urllib2.urlopen(
        'http://connpass.com/api/v1/event/?event_id=%s' % eventid)
    s = response.read()
    json.loads(s)
    hash = hashlib.sha1(str(time.time())+s).hexdigest()
    with open(os.path.join(JSON_DIR, hash), 'w') as f:
        f.write(s)
    return hash

msg = u'''

Python.jpサイトへの、イベント告知掲載リクエストを受け取りました。

確認のため、以下のURLにアクセスしてリクエストを確定してください。

    %s

ご質問などがありましたら、 contact-pyjug@python.jp までご連絡ください。

'''

def sendmail(mailaddr, url):

    mail = MIMEText(msg % url, _charset='iso-2022-jp')
    mail['From'] = 'noreply@python.jp'
    mail['To'] = mailaddr
    mail['Subject'] = Header(u'Python.jp イベント登録の確認', 'iso-2022-jp')

    p = subprocess.Popen([SENDMAIL, mailaddr], stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    o, e =  p.communicate(mail.as_string())
    if p.returncode:
        print o, e, p.returncode

def main():
    form = cgi.FieldStorage()

    print "Content-Type: text/html"
    print

    print '''<meta http-equiv="Content-type" content="text/html;charset=UTF-8">'''

    eventid = form.getfirst('eventid', '').strip()
    mailaddr = form.getfirst('mailaddr', '').strip()

    if not check(eventid, mailaddr):
        return
    filename = search(eventid)

    url = 'http://www.python.jp/cgi-bin/confirm-connpass-event.py?reqid=%s' % filename
    sendmail(mailaddr, url)

main()
