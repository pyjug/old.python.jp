from pprint import pprint
from cStringIO import StringIO
import re
from urlparse import urlsplit

from yaml import loader

class PyramidLoader(loader.Loader):
    pass

def make_dict_from_mapping (node):
    d = {}
    for pair in node.value:
	k, v = pair
        if type(v).__name__ == 'MappingNode':
  	    d[k.value] = make_dict_from_mapping(v)
        else:
  	    d[k.value] = v.value
    ##print d
    return d

# set up classes for yaml parser
class fragment:
    ''' an inline fragment which contains data and a template
    '''
    def __init__(self, node):
        d = make_dict_from_mapping(node)
        self.template = d.get('template',None)
        self.locals = d.get('local',{})
        self.globals = d.get('global',{})
        self.file = d.get('file',None)

    def __eq__(self,other):
        if self.template == other.template and \
           self.locals == other.locals and \
           self.globals == other.globals and \
           self.file == other.file:
            return True
        else:
            return False

    def __ne__(self,other):
        if self.template == other.template and \
           self.locals == other.locals and \
           self.globals == other.globals and \
           self.file == other.file:
            return False
        else:
            return True

class fragmentFile:
    ''' A file fragment which points at another yaml file
    '''
    def __init__(self, node):
        self.file = node

    def __eq__(self,other):
        return self.file == other.file

    def __ne__(self,other):
        return self.file != other.file

def fragmentConstructor(constructor, node):
    if type(node).__name__ == 'MappingNode':
        return fragment(node)
    else:
        return fragmentFile(node)


class rest(str):
    ''' a rest string for converting to html
    '''
    pass

class restfile(str):
    ''' a rest file for converting to html
    '''
    pass

class html(str):
    ''' a html block for converting to html
    '''
    pass

class htmlfile(str):
    ''' a html file for converting to html
    '''
    pass

class htfile(str):
    ''' a ht file for converting to html
    '''
    pass

class wikiurl(str):
    ''' a ht file for converting to html
    '''
    pass

class htfiledata:
    ''' a ht file for converting to ht file datafile and key
    '''
    def __init__(self,node):
        self.file = node['file']
        self.key = node.get('key',None)

    def __eq__(self,other):
        return self.file == other.file and self.key == other.key

    def __ne__(self,other):
        return self.file != other.file or self.key != other.key

class restfiledata:
    ''' a ht file for converting to ht file datafile and key
    '''
    def __init__(self,node):
        self.file = node['file']
        self.key = node.get('key',None)

    def __eq__(self,other):
        return self.file == other.file and self.key == other.key

    def __ne__(self,other):
        return self.file != other.file or self.key != other.key


class rhref(str):
    ''' relative href
    '''

class ahref(str):
    ''' absolute href
    '''

def url(text):
    ''' Factory to convert a string into a label and href (href is last space delimited item in string)
    '''
    # Split off the last space separated string for the url (rest is label/title)
    t = text.split(' ')
    label = ' '.join(t[:-1])

    # Get the label and possibly the title
    getlabelparts = re.compile('([^{}]*)(?: {(.*)})?$')
    m = getlabelparts.match(label)
    if m:
        label,title = m.groups()
    else:
        title = None
    if title is None:
        title = ''

    # Split the url up to check the prefix and whether it is an absolute url
    url = t[-1]
    urlparts = urlsplit(url)
    if urlparts[0] != '' or urlparts[2].startswith('/'):
        url = ahref(url)
    else:
        url = rhref(url)

    return {'href': url, 'label': label, 'title': title}

def linktree(node):
    ''' nav directive creates a tree of data/children nodes from an indented list of strings
    '''
    return parseIndentedList(node,url)

class sectionnav(list):
    ''' section navigation (inherited)
    '''
    def __init__(self, node):
        list.__init__(self)
        self.extend(parseIndentedList(node,url))


class breadcrumb(str):
    ''' a marker for the breadcrumb renderer
    '''
    def __init__(self,node):
        fields = node.split()
        self.file = fields[0]
        self.name = fields[1]

class acquire(str):
    ''' A marker for for extracting data from another fragment (This may
        cause problems as the target data may not be available at the point of flattening)
    '''
    def __init__(self,node):
        fields = node.split()
        self.file = fields[0]
        self.name = fields[1]
        self.template = ''

def pathconstruct(pathstring):
    return str(pathstring)


def context(node):
    raise RuntimeError("Contexts not supported")
    ##return core.Context(node)

class Stack:

    def __init__(self, indent, pointer):
        self.indent = indent
        self.pointer = pointer
        self.indentStack = []
        self.pointerStack = []

    def push(self,indent):
        self.indentStack.append(self.indent)
        self.pointerStack.append(self.pointer)
        self.indent = indent
        self.pointer = self.pointer[-1]['children']

    def pop(self):
        self.indent = self.indentStack.pop()
        self.pointer = self.pointerStack.pop()

    def prevIndent(self):
        return self.indentStack[-1]

def stripAndCountIndent(line):
    lstripline = line.lstrip()
    return lstripline, len(line)-len(lstripline)

def parseIndentedList(text, factory):

    lines = text.split('\n')
    data = {'children':[]}

    # skip any empty lines
    while lines[0].strip() == '':
        lines = lines[1:]

    # this should be the first non-empty line
    trimline, newindent = stripAndCountIndent(lines[0])
    stack = Stack(newindent,data['children'])

    for line in lines:
        if line.strip() == '':
            continue
        trimline, newindent = stripAndCountIndent(line)
        if newindent > stack.indent:
            stack.push(newindent)

        if newindent < stack.indent:
            while newindent < stack.indent:
                stack.pop()
            if newindent != stack.indent:
                raise KeyError

        stack.pointer.append( {'data':factory(trimline), 'children':[] } )

    return data['children']

# Set up type registry
_typeRegistry = {
    ('yaml.org','2002','fragment'): fragmentConstructor,
    ('yaml.org','2002','rest'): rest,
    ('yaml.org','2002','restfile'): restfile,
    ('yaml.org','2002','url'): url,
    ('yaml.org','2002','linktree'): linktree,
    ('yaml.org','2002','sectionnav'): sectionnav,
    ('yaml.org','2002','breadcrumb'): breadcrumb,
    ('yaml.org','2002','acquire'): acquire,
    ('yaml.org','2002','html'): html,
    ('yaml.org','2002','htmlfile'): htmlfile,
    ('yaml.org','2002','htfile'): htfile,
    ('yaml.org','2002','htfiledata'): htfiledata,
    ('yaml.org','2002','restfiledata'): restfiledata,
    ('yaml.org','2002','wikiurl'): wikiurl,
    ('python.yaml.org','2002','object:pyramid.path.path'): pathconstruct,
}

for vartype, factory in _typeRegistry.items():
    tld, year, name = vartype
    tag_url = u'!' + name
    PyramidLoader.add_constructor(tag_url, factory)
