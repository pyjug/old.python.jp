#!/usr/bin/env python
# -*- coding: utf-8
import cgi, re, json, urllib2

form = cgi.FieldStorage()

print "Content-Type: application/json"
print

eventid = form.getfirst('eventid', '')

def search(eventid):
    response = urllib2.urlopen(
        'http://connpass.com/api/v1/event/?event_id=%s' % eventid)
    s = response.read()
    ret = json.loads(s)
    if ret['results_returned'] == 1:
        title = ret['events'][0]['title']
        return json.dumps(title)

eventid = re.match(r'^\d+$', eventid).group()
if eventid:
    ret = search(eventid)
    if ret:
        print ret

