#!/usr/bin/python

import os, glob, sys
import urllib2

def update_feed(fn):
    f = open(fn, 'r')
    url = f.readline().strip()
    f.close()

    try:
        input = urllib2.urlopen(url)
    except urllib2.HTTPError, exc:
        print >>sys.stderr, url, ':', exc
    else:
        info = input.info()
	output = open(os.path.join('cache', os.path.basename(fn)), 'w')
	while True:
	    data = input.read(1024)
	    if data == "": break
	    output.write(data)
	output.close()

  
def main ():
    filenames = glob.glob('*.feed')
    for fn in filenames:
        update_feed(fn)

if __name__ == '__main__':
    main()
