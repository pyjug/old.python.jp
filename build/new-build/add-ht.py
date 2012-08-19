#!/usr/bin/python

# Script to process the tree and generate content.ht files for those
# directories that lack them.

import os, sys
import optparse
import build_util

options = None

def log (msg, *args, **kw):
    """Log messages to stderr; higher levels are less important.
    Use level 0 for reporting errors.
    """
    level = kw.get('level', 1)
    if options.verbose >= level:
        print >>sys.stderr, ' '*(level-1) + (msg % args)

def fix_indented_list (S):
    if S is None:
        return None
    
    S = S.strip()
    S = '\n\t' + S.replace('\n', '\n\t')
    S = S.expandtabs()
    return S
    
def add_ht (dirpath, filenames):
    # Already has a file -- nothing to do.
    if 'content.ht' in filenames:
        return

    # Look for content
    filename, msg = build_util.read_content_file(dirpath)
    if msg is None:
        log('Skipping directory without content: %s', dirpath)
        return

    if filename.endswith('/content.rst'):
        index_yml, nav_yml = build_util.read_yaml_files(dirpath)
        headers = [('Content-type', 'text/x-rst')]
        if index_yml is not None:
            for hdr in ('title', 'description', 'keywords'):
                v = (index_yml.globals.get(hdr) or
                     index_yml.locals.get(hdr))
                if isinstance(v, basestring):
                    headers.append((hdr, v))

        if nav_yml is not None:
            aux = nav_yml.globals.get('aux')
            aux = fix_indented_list(aux)
            if aux:
                headers.append(('Quick-links', aux))
            nav = nav_yml.globals.get('nav')
            nav = fix_indented_list(nav)
            if nav:
                headers.append(('Nav', nav))
            
        log('Writing new content.ht file in %s', dirpath)
        ##dirpath = '/tmp'
        f = open(os.path.join(dirpath, 'content.ht'), 'w')
        for hdr, value in headers:
            f.write('%s: %s\n' % (hdr.capitalize(), value))
        f.write('\n')
        f.write(msg.get_payload())
        f.close()
        
        
    
def main ():
    global options
    
    parser = optparse.OptionParser()
    parser.add_option("-d", "--data", dest="data",
        help="directory of input tree",
        metavar="DATA")
    parser.add_option("-v", "--verbose", action="count",
        dest="verbose", default=0,
        help="print status messages to stdout")
    (options, args) = parser.parse_args()

    build_util.walk_tree(options.data, add_ht)


if __name__ == "__main__":
    main()

