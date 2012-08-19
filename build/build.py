#! /usr/bin/env python

"""
Build the Python.org site.

Usage: build.py [options] [arguments]

Arguments are paths of subdirectories to build.

Options:

-k, --keep-going  Continue building past errors if possible.

-r, --relative    Continue building past errors if possible.

-p, --no-peps     Skip the generation of PEP output.

-f, --force-peps  Force the generation of PEPs

-q, --quiet       Turn off verbose messages.

-n, --new         Use new build script

-h, --help        Print this help message and exit.
"""

import sys
import os
import codecs
import getopt
import shutil


PEPS_DATA_DIR = '../data/dev/peps'


class Settings:

    # defaults:
    verbose = True
    keep_going = False
    relative_urls = True
    build_peps = True
    force_peps_rebuild = False
    new_build = False
    
settings = Settings()


def log(message):
    if settings.verbose:
        print message

def cmd(command):
    log(command)
    child = os.popen(command)
    data = child.read()
    err = child.close()
    if err:
        raise RuntimeError('%s failed w/ exit code %d' % (command, err))
    return data


def build(args):
    # move to directory containing this module:
    # XXX: doesn't work when simply doing 'python build.py'
    os.chdir(os.path.dirname(main.func_code.co_filename))
    # use the Docutils that comes with PEPs,
    # for the current process:
    sys.path.insert(1, os.path.abspath('peps'))
    # and for future os.popen processes:
    PYTHONPATH = ['./peps']
    if 'PYTHONPATH' in os.environ:
        PYTHONPATH.append(os.environ['PYTHONPATH'])
    os.environ['PYTHONPATH'] = os.pathsep.join(PYTHONPATH)
    if not os.path.isdir('out'):
        os.mkdir('out')
    if settings.build_peps:
        build_peps()
    build_site(args)
    print "Done!"

def build_peps():
    import pep2pyramid
    # Obtain/update peps and reconvert for pyramid
    print "Converting PEPs to pyramid"
    os.chdir('peps')
    pep2pyramid.settings.verbose = settings.verbose
    pep2pyramid.settings.force_rebuild = settings.force_peps_rebuild
    pep2pyramid.settings.keep_going = settings.keep_going
    pep2pyramid.settings.dest_dir_base = PEPS_DATA_DIR
    # build all PEPs:
    pep2pyramid.build_peps()
    os.chdir(os.pardir)

def build_site(args):
    print "Rebuilding website"
    if settings.new_build:
        command = 'new-build/build.py --cache=pydotorg.cache -v -d data -o out -r images,styles,files,js'
    else:
        command = 'pyramid --data data --out out --resources images,styles,files,js'
        
    if settings.keep_going:
        command += ' --keepgoing'
    if settings.relative_urls:
        command += ' --relativeurls'
    output = cmd('%s %s' % (command, ' '.join(args)))
    if settings.verbose:
        print output
    # Copy RSS feed into place where most existing consumers expect it
    print "Copying RSS feed into place"
    shutil.copyfile('out/news/rdf/index.html', 'out/channews.rdf')

def usage(code, msg=''):
    """Print usage message and exit.  Uses stderr if code != 0."""
    if code == 0:
        out = sys.stdout
    else:
        out = sys.stderr
    print >> out, __doc__ % globals()
    if msg:
        print >> out, msg
    sys.exit(code)

def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    try:
        opts, args = getopt.getopt(
            argv, 'hfknrpq',
            ['help', 'force-peps', 'keep-going', 'relative', 'no-peps',
             'quiet', 'new'])
    except getopt.error, msg:
        usage(1, msg)
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage(0)
        elif opt in ('-f', '--force-peps'):
            settings.force_peps_rebuild = True
        elif opt in ('-k', '--keep-going'):
            settings.keep_going = True
        elif opt in ('-n', '--new'):
            settings.new_build = True
        elif opt in ('-r', '--relative'):
            settings.relative_urls = True
        elif opt in ('-p', '--no-peps'):
            settings.build_peps = False
        elif opt in ('-q', '--quiet'):
            settings.verbose = False
    build(args)


if __name__ == "__main__":
    main()
