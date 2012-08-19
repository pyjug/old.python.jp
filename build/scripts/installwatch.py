#!/usr/bin/python
import sys, os
from pyramid.path import path
from optparse import OptionParser

VERBOSE=True

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

def parse(log):
    result = set()
    failures = False
    for line in log:
        line = line.rstrip()
        from_,to = line.split(' -> ')
        assert to[0] == "`" and to[-1]=="'"
        to = path(to[1:-1]).abspath()
        result.add(to)
    return result

def sync(frompath,topath,installpathlog):
    # get the log file
    logpath = path(installpathlog)
    logtext = logpath.lines()
    oldlog = parse(logtext)
    
    #move old log out of way
    logpath.move('installwatch-old.log')

    try:
        cmd('LANG=C cp -v -r %s/* %s/. >%s' % (frompath,topath,logpath))
    except:
        log('installing failed')
        oldlogpath = path('installwatch-old.log')
        oldlogpath.move(logpath)
        raise
    
    #parse new log
    newlogtext = logpath.lines()
    newlog = parse(newlogtext)
    
    #get log differences (for deletes)
    deletedpaths = oldlog - newlog
    
    #walk and delete the files that don't exist anymore
    for file in deletedpaths:
        if file.isfile() and not file.isdir():
            log('removing %s' % file)
            file.remove()
    

def main(options,args):
    sync(options.frompath,options.topath,options.installpathlog)


def parseOptions():
    parser = OptionParser()
    parser.add_option("-f", "--from", dest="frompath", help="where to copy from", metavar="FROM")
    parser.add_option("-t", "--to", dest="topath", help="where to copy to", metavar="TO")
    parser.add_option("-l", "--log", dest="installpathlog", help="Which install path log to use for syncing", metavar="INSTALLPATHLOG")
    (options, args) = parser.parse_args()
    main(options,args)

if __name__ == "__main__":
    parseOptions()
