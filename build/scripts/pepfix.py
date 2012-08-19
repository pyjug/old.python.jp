#!/usr/bin/python
import re
import shutil
import sys

## Usage: cd into the directory, run this script with the offending filename as
## arg, check result, delete *.old


## replace URLs containing peps//doc/pep with /doc/peps
## remove site as well - allows later move from www.python to archive.python

## match the whole url only in href and not in body of doc
pat = re.compile(r'"http://[-a-zA-Z0-9]+.python.org/peps//doc/peps/pep-([0-9]+)"')

# pattern2 is to clean up URLs in text of document in the form <a href="blah">Bad link</a>
pat2 = re.compile(r'/peps//doc/peps/(pep-([0-9]+)<)') 

oldtext = open(sys.argv[1]).read()

if pat.search(oldtext):
    # make a backup copy first
    shutil.copy(sys.argv[1], sys.argv[1]+'.old')
    newfile = open(sys.argv[1],'w')
    newtext = pat.sub(r'"/doc/peps/pep-\1"', oldtext)
    newtext = pat2.sub(r'/doc/peps/\1', newtext)
    newfile.write(newtext)  
    newfile.close()
