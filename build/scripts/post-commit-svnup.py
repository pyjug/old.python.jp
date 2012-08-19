#!/usr/bin/python2.6

import os
import sys
from datetime import datetime


os.umask(002)

VERBOSE=True

BUILD_CHECKOUT_DIR='/data/website-build/build'
WWW_DIR = '/data/ftp.python.org/pub/www.python.org'
UPDATEDIRS = ['data','styles','js','files','images']

BUILDINPROCESS = os.path.join(BUILD_CHECKOUT_DIR, 'status/buildinprocess')
BUILDQUEUED = os.path.join(BUILD_CHECKOUT_DIR, 'status/buildqueued')
PEPQUEUED = os.path.join(BUILD_CHECKOUT_DIR, 'status/pepqueued')
PEPDIR = os.path.join(BUILD_CHECKOUT_DIR, 'data/dev/peps')
JOBSDIR = os.path.join(BUILD_CHECKOUT_DIR, 'data/community/jobs')
JOBSOUTDIR = os.path.join(BUILD_CHECKOUT_DIR, 'out/community/jobs')

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

def logStatus(revision,status):
    log('logStatus(%s,%s)'% (revision,status))
    statusfile = os.path.join(BUILD_CHECKOUT_DIR, 'status/updates/index.html')
    lastsuccessfulrevisionfile = os.path.join(BUILD_CHECKOUT_DIR, 'status/lastrev.txt')
    svnlogfile = os.path.join(BUILD_CHECKOUT_DIR, 'status/log/index.html')
    log('writing %s' % statusfile)
    log('writing %s' % lastsuccessfulrevisionfile)
    log('writing %s' % svnlogfile)

    fp = file(statusfile,'a')
    fp.write('%s : update to revision %s %s\n' %
             (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), revision, status))
    fp.close()

    # Log the changes
    print 'before success check %s' % status
    if status == 'succeeded' and revision != '':
        print 'inside success check'
        # get the last successful revision number
        fp = file(lastsuccessfulrevisionfile,'r')
        lasttext = fp.read().strip()
        try:
            last = str( int(lasttext)+1 )
            last = int(lasttext)
        except ValueError:
            log('last revision int conversion failed')
            last = 'HEAD'
        fp.close()

        # get the log between the last successful and this revision and save it
        svnlog = cmd(
            'svn log file:///data/repos/www/trunk/beta.python.org/build/data '
            '-r %s:%s' % (last,revision))
        fp = file(svnlogfile,'w+')
        fp.write('<pre>')
        fp.write(svnlog)
        fp.close()

        # Log the revision if it was successful
        fp = file(lastsuccessfulrevisionfile,'w+')
        fp.write(revision)
        fp.close()

    return

def update(revision):
    if os.path.exists(BUILDINPROCESS):
        return

    open(BUILDINPROCESS, "w").close()
    log(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    log('building')

    # pre hooks
    try:
        # Get the svn repo synchronised with the post commit version...
        os.chdir(BUILD_CHECKOUT_DIR)
        if revision != '':
            for d in UPDATEDIRS:
                cmd('whoami')
                try:
                    cmd('svn up %s --revision %s'%(d, revision))
                except RuntimeError, error:
                    log('%s: %s' % (error.__class__.__name__, error))

        # Build this directory
        cmd('./scripts/server-build.py')

        # perform a copy and sync from out to the target directory referring
        # to a previous install log for changes.
        cmd('./scripts/installwatch.py -f out -t %s -l installwatch.log'
            % WWW_DIR)
        os.remove(BUILDINPROCESS)
        logStatus(revision,'succeeded')

    except:
        os.remove(BUILDINPROCESS)
        logStatus(revision,'failed')


def update_jobs():
    log('Rebuilding jobs.rss')
    try:
        cmd("%s/jobs2rss.py %s %s"%(JOBSDIR, JOBSDIR, JOBSOUTDIR))
    except Exception, (errno, errstr):
        log("Exception while updating jobs feed (%s: %s)"%(errno, errstr))
    log('Rebuilt jobs.rss')


def main():
    """
    Just gets the arguments which should be repos and rev from the subversion
    post commit hook
    """
    if os.path.exists(PEPQUEUED):
        os.remove(PEPQUEUED)
        os.chdir(os.path.join(BUILD_CHECKOUT_DIR, "peps"))
        try:
            cmd("/usr/local/bin/hg pull --update")
        except RuntimeError, error:
            log('%s: %s' % (error.__class__.__name__, error))
        cmd("make pep-0000.txt")
        cmd("./pep2pyramid.py --force -d %s" % PEPDIR)
        cmd("./pep2rss.py %s" % PEPDIR)
        open(BUILDQUEUED, "w").close()


    if os.path.exists(BUILDINPROCESS):
        # allow new checkins to queue a new build during another build
        # (leave BUILDQUEUED in place)
        return

    if os.path.exists(BUILDQUEUED):
        with open(BUILDQUEUED) as f:
            revision = f.read()
        log('revision %s' % revision)
        os.remove(BUILDQUEUED)
        update(revision)

        update_jobs()


if __name__ == "__main__":
    main()
