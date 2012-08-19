#!/usr/bin/python2.6
import os
os.umask(002)


BUILD_CHECKOUT_DIR='/data/website-build/build'

VERBOSE = True

def log(message):
    if VERBOSE:
        print message

def cmd(command):
    log(command)
    child = os.popen(command)
    data = child.read()
    err = child.close()
    if err:
        raise RuntimeError, '%s failed w/ exit code %d' % (command, err)
    return data

os.chdir(BUILD_CHECKOUT_DIR)

# Rebuild 
##cmd('pyramid -k -v -d data -o out -r images,styles,files,js --relativeurls')
cmd('new-build/build.py --cache=/data/tmp/pydotorg.cache -v '
    '-d data -o out -r images,styles,files,js')

# Copy RSS feed into place where most existing consumers expect it
lines = file('out/news/rdf/index.html').readlines()
open('out/channews.rdf','w').writelines(lines)
