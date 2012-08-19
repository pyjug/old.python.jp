#!/usr/bin/env python2.4

"""
   This module is a standalone program for building the static HTML content of
   www.python.org from the various content documents and metadata.  It
   implements a dependency-checking system and only rebuilds those documents
   which are out of date.
"""

import os, sys, time, stat
import re, shutil, optparse
import cgi, email, cPickle
import pprint, copy, random

import yaml
import feedparser

#from mako.template import Template

import build_util, rst_html, pyramid_yaml

#
# Global variables
#

options = None
basic_template = None

def log (msg, *args, **kw):
    """Log messages to stderr; higher levels are less important.
       Use level 0 for reporting errors.
    """

    level = kw.get('level', 1)
    if options.verbose >= level:
        print >>sys.stderr, ' '*(level-1) + (msg % args)

def decode_string (S):
    "Try decoding a string in both supported encodings"

    try:
        return S.decode('utf-8')
    except UnicodeError:
        return S.decode('iso-8859-1')

def check_safe_filename (fn):
    "Raises an exception if there's something suspicious about a filename"

    if '/' in fn:
        raise ValueError("Subdirectories are forbidden")
    elif fn == '.':
        raise ValueError("Using '.' is forbidden")
    elif fn == '..':
        raise ValueError("Using '..' is forbidden")

def get_program_directory ():
    "Return the path to the directory containing the build software."

    import __main__
    return os.path.dirname(__main__.__file__)

def get_template_path (fn):
    """Given a filename for a template, return the full path to that file
       within the template directory.
    """

    fn = get_template_filename(fn)
    exec_path = get_program_directory()
    tmpl_path = os.path.join(exec_path, fn)
    return tmpl_path

def get_template_filename (fn):
    "Return the right filename for a template."

    check_safe_filename(fn)
    if not fn.endswith('.tmpl'):
        fn += '.tmpl'
    return fn

prog_dir = get_program_directory()

from mako.lookup import TemplateLookup
pdo_lookup = TemplateLookup(
    directories=[prog_dir, os.path.join(prog_dir, 'fragments')],
    input_encoding='utf-8',
    module_directory='/tmp/mako',
    default_filters=['decode.utf8'])

def read_template (fn):
    "Read and parse a template file, returning the Template object."

    tmpl_name = get_template_filename(fn)
    return pdo_lookup.get_template(tmpl_name)

def read_fragment (fn):
    "Read the contents of a file containing a fragment of HTML"

    check_safe_filename(fn)
    if not fn.endswith('.html'):
        fn += '.html'
    return pdo_lookup.get_template(fn)

#
# Functions made available to the code running inside templates
#

def read_rss (fn):
    "Read and parse an RSS file that has already been fetched."

    check_safe_filename(fn)

    import __main__
    exec_path = os.path.dirname(__main__.__file__)
    rss_path = os.path.join(exec_path, 'rss', 'cache', fn)
    if not rss_path.endswith('.feed'):
        rss_path += '.feed'

    try:
        f = open(rss_path, 'r')
    except IOError:
        print >>sys.stderr, 'RSS file %r not found; run "make rss"' % fn
        return []

    feed_xml = f.read()
    feed = feedparser.parse(feed_xml)
    f.close()

    return feed['items']

def read_news ():
    """Read the newsindex.yml file, returning a list of dictionaries
       that contain information about each news item.
    """

    input = open(os.path.join(options.data, 'newsindex.yml'), 'r')
    data = yaml.load(input, pyramid_yaml.PyramidLoader)
    input.close()
    result = []
    for mapping_node in data.globals['news']:
        d = {}
        L = list(mapping_node.value)
        for key_node, value_node in L:
            key = key_node.value
            item_html = value_node.value

            if key == 'description':
                item_html = rst_html.process_rst('newsindex.yml', item_html)
                item_html = item_html.strip()

                if item_html.startswith('<p>'): item_html = item_html[3:]
                if item_html.endswith('<p>'): item_html = item_html[:-3]

            d[key_node.value] = item_html
        result.append(d)

    return result

def read_sigs ():
    """Read the sigindex.yml file, returning a list of dictionaries
       that contain information about each SIG.
    """

    input = open(os.path.join(
        options.data, 'community', 'sigs', 'sigindex.yml'), 'r')

    data = yaml.load(input, pyramid_yaml.PyramidLoader)
    input.close()
    result = []
    for mapping_node in data.globals['sigs']:
        d = {}
        L = list(mapping_node.value)
        for key_node, value_node in L:
            key = key_node.value
            d[key_node.value] = value_node.value
        result.append(d)

    return result

def read_retired_sigs ():
    """Read the retired/sigindex.yml file, returning a list of dictionaries
       that contain information about each old SIG.
    """

    input = open(os.path.join(
        options.data, 'community', 'sigs', 'retired', 'sigindex.yml'), 'r')

    data = yaml.load(input, pyramid_yaml.PyramidLoader)
    input.close()
    result = []
    for mapping_node in data.locals['sigs']:
        d = {}
        L = list(mapping_node.value)
        for key_node, value_node in L:
            key = key_node.value
            d[key_node.value] = value_node.value
        result.append(d)

    return result

def choose_random (obj):
    if isinstance(obj, dict):
        return random.choice(dict.values())
    else:
        return random.choice(obj)

def anchorify (data):
    "Turn the data into something suitable for an anchor"

    import string
    nulltrans = string.maketrans('', '')
    data = str(data).translate(nulltrans, " ,'\"<>&+:.")
    return data

class Link:
    """Class representing hyperlinks in the navigation tree.

       Instance attributes:
       .href       Target of link
       .link_text  Text to use inside <a>...</a>.
       .title      Text to use as the 'title' attribute of <a>
       .selected   Boolean; true if this link should be displayed in
                   'selected' style.
    """

    def __init__ (self, href, link_text, title=None, selected=False):
        self.href = href
        self.link_text = link_text
        self.title = title
        self.selected = selected

    def copy (self):
        new = Link(self.href, self.link_text, self.title, self.selected)
        return new

    def __repr__ (self):
        return '<%s at 0x%x: href=%s link-text=%r>' % (
            self.__class__.__name__,
            id(self), self.href,
            self.link_text)

    def as_html (self):
        "Return a Unicode string holding the corresponding <a> element."

        s = t = ''
        if self.title:
            t = ' title="%s"' % cgi.escape(self.title, quote=True)
        if self.selected:
            s = ' class="selected"'

        return u'<a href="%s"%s%s>%s</a>' % (
            cgi.escape(self.href), t, s,
            cgi.escape(self.link_text))

#
# Caching functions
#

_cache = {}
def cache (path, nav, title, label):
    if nav is not None:
        nav = nav[:]
    _cache[path] = (nav, title, label)

def get_cached_nav (path):
    ##print sorted(_cache.keys())
    return _cache.get(path, (None, None, None))[0]

def get_cached_title (path):
    return _cache.get(path, (None, None, None))[1]

def get_cached_label (path):
    return _cache.get(path, (None, None, None))[2]

def read_cache ():
    global _cache
    if options.cache is not None:

        if os.path.exists(options.cache):
            rebuild_cache = False
            f = open(options.cache, 'rb')
            try:
                _cache = cPickle.load(f)
            except EOFError:
                f.close()
                rebuild_cache = True
        else:
            # Need to force rebuild of all when there's no cache present yet
            rebuild_cache = True

        if rebuild_cache:
            print "Forcing rebuild of all to generate cache"
            _rebuild_cache[''] = 1

def save_cache ():
    if options.cache is not None:
        f = open(options.cache, 'wb')
        cPickle.dump(_cache, f)
        f.close()

#
# Dependency checking functions
#

def is_newer(name1, name2):
  """Returns whether file with name1 is newer than file with name2.

     Returns False if name1 doesn't exist and returns True if name2 doesn't
     exist.
  """

  if not os.path.exists(name1):
    return False
  if not os.path.exists(name2):
    return True

  mod_time1 = os.stat(name1)[stat.ST_MTIME]
  mod_time2 = os.stat(name2)[stat.ST_MTIME]
  return mod_time1 > mod_time2

read_news_users = ['homepage', 'news-archive', 'rss']

def get_input_output_files(dirpath, msg):
    """Get (input, output) where input is a list of files used as input when
       building the given output page
    """

    input = ['index.yml', 'nav.yml', 'content.ht', 'content.rst', 'body.html']
    input = [os.path.join(options.data, dirpath, x) for x in input]

    output_html = os.path.join(options.out, dirpath, 'index.html')

    # Add the template to the dependency list.
    template = msg.get('Template', 'pydotorg')
    input.append(get_template_path(template))
    if template in read_news_users:
        input.append(os.path.join(options.data, 'newsindex.yml'))
    exec_path = get_program_directory()
    for fragment in msg.get('Fragments', '').split():
        if not fragment.endswith('.html'):
            fragment += '.html'
        input.append(os.path.join(exec_path, 'fragments', fragment))

    return (input, output_html)

def input_newer(input, output_html):
    """Check if any of the input files are newer than the output file.

       Return tuple (any_newer, yml_newer)
    """

    any_newer = False
    yml_newer = False
    for i in input:
        if is_newer(i, output_html):
            any_newer = True
            if i.endswith('.yml'):
                yml_newer = True
                break

    return any_newer, yml_newer

_rebuild_cache = {}

def must_rebuild(relpath):
    for force_dir in _rebuild_cache.keys():
        if relpath.startswith(force_dir):
            return True
    return False

#
# Navigation list processing.
#
# A list of navigation links is of the form:
# [ (<Link object 1>, sequence of children),
#   (<Link object 2>, sequence of children) ...]
#
# The Mako template takes these lists and renders them properly.
# The hard part is calculating the list in the first place.
#

def parse_nav_list (content):
    """Takes the content of an indented navigation list as recorded in
       a RFC-822 header line or YAML file.  Lists look like this:

       About {About The Python Language} about
       News news
       Documentation doc
       Download download

       Returns a navigation list.
    """

    if content is None:
        return []

    content = decode_string(content)

    # Parse the indented list.
    def identity(x): return x
    data = pyramid_yaml.parseIndentedList(content, identity)

    title_pat = re.compile('[{](.*)[}]')

    def make_link (d):
        "Take a single line and return the corresponding Link object."

        line = d['data']
        # Look for {...title...} and extract it
        m = title_pat.search(line)
        if m is not None:
            title = m.group(1)
            line = title_pat.sub('', line)
        else:
            title = None

        L = line.rsplit()
        url = L[-1]
        label = ' '.join(L[:-1])
        # XXX fill in selected field
        return Link(url, label, title, selected=False)

    result = []
    for d in data:
        link = make_link(d)
        children = []
        for c in d['children']:
            c_link = make_link(c)
            children.append((c_link, ()))
        result.append((link, tuple(children)))

    return tuple(result)

def trim_nav_links (nav):
    """Remove common whitespace prefix from all the lines in the 'Nav:'
       header, dropping blank lines.
    """

    if nav is None:
        return None

    nav = nav.expandtabs()
    lines = [line for line in nav.split('\n')
             if line.strip() != ""]
    if lines:
        min_ws = min([len(line) - len(line.lstrip()) for line in lines])
        for i, line in enumerate(lines):
            lines[i] = lines[i][min_ws:]
        nav = '\n'.join(lines)
        return nav
    else:
        return None

def normalize_nav_link(href):
    assert not href.startswith('http://') and not href.startswith('.')
    href = '/' + href + '/'
    return re.sub('/{2,}', '/', href)

def expand_nav_links(context, nav):
    "Expand nav links in given list so they are full paths"

    if nav is None:
        return None

    # Get path to current position
    context_path = '/'.join(context)

    # Join path to children into urls in child nav
    child_nav = copy.deepcopy(nav)
    for (clink, cchild) in child_nav:
        href = clink.href
        if href == '.':
            href = ''
        if href.startswith('.'):
            print "Warning:  Found relative url", href, "in", context_path
        elif not href.startswith('http://'):
            if not href.startswith('/'):
                href = context_path + '/' + clink.href
            clink.href = normalize_nav_link(href)

    return child_nav

def splice_nav_links (context, parent_nav, nav):
    """Given a parent and child navigation list, and a the path context,
       look through the parent and splice in the child at the link
       that matches the last component in the given context path.
    """

    if len(context) > 0:
        last_component = context[-1]
    else:
        last_component = None
    context_path = normalize_nav_link('/'.join(context))

    new_nav = list(parent_nav)          # Make a copy to avoid
                                        # modifying the cached copy.

    for i, (link, children) in enumerate(new_nav):
        link_copy = link.copy()         # Copy links, too
        ##print link_copy.href, last_component
        if link_copy.href == context_path:
            # Aha!  this is the branch of the tree where we are.
            # Insert the navigation sublist and mark the parent as 'selected'.
            children = expand_nav_links(context, nav)
            link_copy.selected = True

        new_nav[i] = (link_copy, children)

    return new_nav

def rebuild_directory (dirpath, filenames):
    """Generate content for a single directory.

       'dirpath' is the path to the input data; the output
       directory is calculated.
       'filenames' is the list of files in the directory.
    """

    # Figure out the destination path.
    assert dirpath.startswith(options.data)
    rel_path = dirpath[len(options.data):]
    output_dir = os.path.join(options.out, rel_path)
    output_path = os.path.join(output_dir, 'index.html')

    if options.rebuilddirs:
        skip = True
        for rb_dir in options.rebuilddirs:
            if rel_path == rb_dir or rel_path.startswith(rb_dir + '/'):
                skip = False
        if skip:
            log('Skipping directory %s', dirpath, level=3)
            return

    # Split apart the path portion of the URL (e.g. /about/community/)
    # into its components.
    components = rel_path.strip('/').split('/')
    components = filter(None, components)

    filename, msg = build_util.read_content_file(dirpath)
    if msg is None:
        log('Skipping directory without content: %s', dirpath)
        return

    # Create output directory and check dependencies
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        any_newer = True
        yml_newer = True
    elif not options.cache:
        any_newer = True
        yml_newer = True
    elif must_rebuild(rel_path):
        any_newer = True
        yml_newer = True
    else:
        any_newer, yml_newer = input_newer(
            *get_input_output_files(rel_path, msg))

    # Whenever yml changes, all sub-pages need to be rebuilt too
    if yml_newer:
        _rebuild_cache[rel_path] = 1

    # Copy non-HTML/YML files if they are newer
    for fn in filenames:
        if fn.endswith('~') or fn.endswith('.swp'):
            continue

        base, ext = os.path.splitext(fn)
        if (ext not in ('.rst', '.ht', '.yml') and
            fn not in ('content.html', 'body.html')):

            src_file = os.path.join(dirpath, fn)
            dest_file = os.path.join(output_dir, fn)

            if is_newer(src_file, dest_file):
                log(' Copying file: %s', fn, level=2)
                shutil.copy(src_file, dest_file)
            else:
                log(' File up to date: %s', fn, level=3)

    if not any_newer:
        return

    log('Rebuilding directory %s', dirpath, level=2)
    log(' Output will be written to %s', output_path, level=3)

    kw = {'rss':read_rss, 'random':choose_random, 'read_news':read_news,
          'read_sigs':read_sigs, 'read_retired_sigs':read_retired_sigs,
          'anchorify':anchorify}

    # Read data from YAML files
    try:
        index_yml, nav_yml = build_util.read_yaml_files(dirpath)
    except Exception, exc:
        print "YAML read error on", dirpath, ":", str(exc)
        return

    kw['title'] = kw['keywords'] = kw['description'] = None
    if index_yml is not None:

        kw['description'] = (
            index_yml.globals.get('metadata', {}).
            get('description'))

        kw['keywords'] = (
            index_yml.globals.get('metadata', {}).
            get('keywords'))

        title = (index_yml.globals.get('title') or
                 index_yml.locals.get('title'))
        if not (isinstance(title, dict) or title is None):
            kw['title'] = title

    # Examine contents of headers
    content_type = msg.get('Content-type', 'text/html')
    text = msg.get_payload()

    kw['keywords'] = msg.get('Keywords', kw['keywords'])
    kw['description'] = msg.get('Description', kw['description'])
    kw['javascript'] = msg.get('Javascript', '').split()
    kw['using'] = parse_nav_list(trim_nav_links(msg.get('Using-Python')))
    kw['fragments'] = msg.get('Fragments', '').split()

    template_name = msg.get('Template')

    # Figure out title
    title = msg.get('Title', kw['title'])
    if title == 'None' or title is None:
        title = 'python.org'
    kw['title'] = title

    # Process the textual contents of the page.
    if content_type == 'text/html' or content_type == 'text/x-ht':
        text = decode_string(text)
    elif content_type == 'text/x-rst':
        text = decode_string(text)
        text = rst_html.process_rst(filename, text)
    elif content_type == 'text/plain':
        text = decode_string(text)
        text = '<pre>' + cgi.escape(text) + '</pre>'
    else:
        log('Unknown content-type %r in %s', content_type, dirpath)
        return

    kw['text'] = text

    # Process sidebar navigation.
    kw['quicklinks'] = []
    if msg.has_key('Quick-links'):
        kw['quicklinks'] = parse_nav_list(trim_nav_links(msg.get('Quick-links')))
    elif nav_yml is not None:
        aux = nav_yml.globals.get('aux')
        if aux is not None:
            log('Using nav.yml in directory %s', rel_path, level=3)
            kw['quicklinks'] = parse_nav_list(aux)

    nav = None
    if msg.has_key('Nav'):
        nav = msg['Nav']
        nav = trim_nav_links(nav)
        if nav:
            nav = parse_nav_list(nav)
    elif nav_yml is not None:
        log('Using nav.yml in directory %s', rel_path, level=3)
        nav = nav_yml.globals.get('nav')
        nav = parse_nav_list(nav)

    # Convert all links in nav to full path
    nav = expand_nav_links(components, nav)

    # Process subnavigation links
    docnav = None
    if msg.has_key('Document-nav'):
        docnav = parse_nav_list(trim_nav_links(msg.get('Document-nav')))
    kw['docnav'] = docnav
    kw['docnav_title'] = msg.get('Document-nav-title', 'About')

    # Find the label for this page, to be used in the breadcrumbs
    page_label = None
    parent_nav = get_cached_nav(os.path.dirname(rel_path))
    context_path = normalize_nav_link('/'.join(components))
    if parent_nav is not None:
        for (link, children) in parent_nav:
            if link.href == context_path:
                page_label = link.link_text
                break

    # Cache the information we have
    cache(rel_path, nav, title, page_label)

    # Make list of all the navigation links for this directory.
    nav_list = []
    for i in range(len(components)+1):
        path = '/'.join(components[:i])
        nav = get_cached_nav(path)
        nav_list.append((i-1, copy.deepcopy(nav)))

    # Splice together the parent and this directory's navigation.
    _, top_nav = nav_list[0]
    if rel_path:
        ##pprint.pprint(nav_list)
        if len(nav_list) > 1:
            child_index, child_nav = nav_list[1]
            child_nav = child_nav or []
            if child_nav and len(nav_list) > 2:
                gc_index, grandchild_nav = nav_list[2]
                grandchild_nav = grandchild_nav or []
                ##print '***', components, gc_index
                if len(components) > (gc_index+1):
                    grandchild_nav = splice_nav_links(components[:gc_index+2],
                                                      grandchild_nav, ())

                child_nav = splice_nav_links(components[:gc_index+1],
                                             child_nav,
                                             grandchild_nav)

            top_nav = splice_nav_links(components[:child_index+1], top_nav,
                                       child_nav)

            #print components, child_index
            #pprint.pprint(nav_list)
            #top_nav = splice_nav_links(components[child_index], top_nav, child_nav,
            #components)

    kw['nav'] = top_nav

    # Figure out the breadcrumbs
    bc = []
    if dirpath != options.data:
        for i in range(1, len(components)):
            comp_path = '/'.join(components[:i])
            comp_title = get_cached_label(comp_path)
            if comp_title is not None:
                bc.append(Link(normalize_nav_link(comp_path), comp_title))

        bc.append(Link('.', page_label or title))
    kw['breadcrumbs'] = bc

    # Read any fragments to be added to the page
    for i, frag in enumerate(kw['fragments']):
        fragment_tmpl = read_fragment(frag)
        frag_html = fragment_tmpl.render_unicode(**kw)
        kw['fragments'][i] = frag_html

    # Render the page.
    assert isinstance(text, unicode)
    if template_name is not None:
        template = read_template(template_name)
    else:
        template = basic_template
    page_text = template.render_unicode(**kw)

    # Write the page
    output = open(output_path, 'w')
    output.write(page_text.encode('utf-8'))
    output.close()

def copy_nosvn(src, dst):
    """Similar to shutil.copytree, but excluding .svn directories.

       Fails on first error, rather than continuing.
    """

    names = os.listdir(src)
    os.makedirs(dst)
    errors = []
    for name in names:
        if name == '.svn':
            continue
        srcname = os.path.join(src, name)
        dstname = os.path.join(dst, name)
        if os.path.isdir(srcname):
            copy_nosvn(srcname, dstname)
        else:
            shutil.copy2(srcname, dstname)
    try:
        shutil.copystat(src, dst)
    except WindowsError:
        # can't copy file access times on Windows
        pass

def execute (args):
    # Read the template
    global basic_template
    basic_template = read_template('pydotorg')

    read_cache()
    if options.rebuilddirs and len(_cache) == 0:
        print >>sys.stderr, ("Cannot specify -R, --rebuilddirs unless "
                             "a cache has been pre-built and specified with "
                             "--cache")
        sys.exit(1)

    if options.erase_existing:
        if os.path.exists(options.out):
            log('Deleting existing %s directory', options.out)
            shutil.rmtree(options.out)

    if not os.path.exists(options.out):
        os.makedirs(options.out)

    start = time.time()

    # Copy resource directories
    if options.resources is not None:
        resources = options.resources.split(',')
        log('Copying resource directories: %s', resources)
        for rsrc in resources:
            dest_path = os.path.join(options.out, rsrc)
            if os.path.exists(dest_path):
                shutil.rmtree(dest_path)
                log('Removing resource directory %s; it already exists',
                    rsrc, level=2)

            log('Copying resource directory %s', rsrc, level=2)
            log('Copying resource directory to %s', dest_path, level=2)
            copy_nosvn(rsrc, dest_path)


    # Rebuild all directories
    build_util.walk_tree(options.data, rebuild_directory, options.keepgoing)

    log('Total time for rebuild: %.1f sec', time.time()-start, level=1)
    save_cache()


def main():
    global options

    parser = optparse.OptionParser(
        usage="%prog",
        version="%prog 1.0")

    parser.add_option("-d", "--data",
        action="store", dest="data",
        help="directory of input tree",
        metavar="DATA")

    parser.add_option("-o", "--out",
        action="store", dest="out",
        help="directory in which to save output (will be emptied)",
        metavar="OUT")

    parser.add_option("-r", "--resources",
        action="store", dest="resources", default=None,
        help="comma separated list of resource directories to copy",
        metavar="RESOURCES")

    parser.add_option("--cache",
        action="store", dest="cache", default=None,
        help="filename for caching tree data",
        metavar="CACHE")

    parser.add_option("-v", "--verbose",
        action="count", dest="verbose", default=0,
        help="print status messages to stdout")

    parser.add_option("-V", "--veryverbose",
        action="store_const", dest="verbose", default=0, const=2,
        help="print all data to stdout")

    parser.add_option("-W", "--veryveryverbose",
        action="store_const", dest="verbose", default=0, const=3,
        help="print all data to stdout")

    parser.add_option("--erase-existing",
        action="store", dest='erase_existing',
        help="erase existing content ???")

    # XXX implement these switches!

    parser.add_option("-R",  "--rebuilddirs",
        action="store", dest="rebuilddirs", default = '',
        help="only rebuild below these comma-separated directories",
        metavar="REBUILDDIRS")

    parser.add_option("-k", "--keepgoing",
        action="store_true", dest="keepgoing", default=False,
        help="keep going past errors if possible")

    parser.add_option("-U", "--update",
        action="store_true", dest="update", default=False,
        help="NOT WORKING DO NOT USE try to build only those pages that have changed")

    parser.add_option("-n", "--relativeurls",
        action="store_true", dest="relativeurls", default=False,
        help="Converts urls from absolute to relative")

    parser.add_option("-P", "--prettify",
        action="store_true", dest="prettify", default=False,
        help="Prettify output - not used on live site")

    options, args = parser.parse_args()

    # Ensure .data and .out are absolute paths that end in '/'.
    options.data = os.path.join(os.getcwd(), options.data).rstrip('/') + '/'
    options.out = os.path.join(os.getcwd(), options.out).rstrip('/') + '/'
    assert options.data.endswith('/')
    assert options.out.endswith('/')

    options.rebuilddirs = filter(None, options.rebuilddirs.split(','))
    execute(args)

if __name__ == "__main__":

    if '--profile' in sys.argv:

        sys.argv.remove('--profile')
        print 'Starting profile'

        import hotshot, hotshot.stats
        prof = hotshot.Profile('newbuild.prof')
        prof.runcall(main)
        prof.close()

        print 'Profile completed'

        stats = hotshot.stats.load('newbuild.prof')
        #stats.strip_dirs()
        stats.sort_stats('time', 'calls')
        stats.print_stats(50)

    else:
        main()
