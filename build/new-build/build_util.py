#!/usr/bin/env python

"""Various utility functions for scripts that work with the 
the Python web site's data.

"""

import os, sys
import email, traceback

import yaml, pyramid_yaml

def walk_tree (path, func, keepgoing=False):
    """(str, str)
    Walks the directory rooted at 'path', and calls func(dirpath, filenames)
    for each directory.
    """
    for dirpath, dirnames, filenames in os.walk(path):
        if '.svn' in dirnames:
            dirnames.remove('.svn')
        try:
            func(dirpath, filenames)
        except:
            if keepgoing:
                print >>sys.stderr, "Error rebuilding directory:", dirpath
                traceback.print_exc()
                print >>sys.stderr, "-"*30
            else:
                raise
            

def read_content_file (dirpath):
    """(str): (str, email.Message)
    Given a directory path, figure out the file holding the content
    for that directory and parse it as an email message.
    """
    # Read page content
    c_ht = os.path.join(dirpath, 'content.ht')
    c_rst = os.path.join(dirpath, 'content.rst')
    body_html = os.path.join(dirpath, 'body.html')
    if os.path.exists(c_ht):
        input = open(c_ht, 'r')
        msg = email.message_from_file(input)
        filename = c_ht
        
    elif os.path.exists(c_rst):
        rst_text = open(c_rst, 'r').read()
        rst_msg = """Content-type: text/x-rst

%s""" % rst_text.lstrip()
        msg = email.message_from_string(rst_msg)
        filename = c_rst
        
    elif os.path.exists(body_html):
        html_text = open(body_html, 'r').read()
        html_msg = """Content-type: text/html

%s""" % html_text.lstrip()
        msg = email.message_from_string(html_msg)
        filename = body_html
    else:
        return None, None

    return filename, msg

#
# YAML functions
#

def read_yaml (path):
    """Read a YAML file if possible, returning None if there's
    no such file.
    """
    if not os.path.exists(path):
        return None

    input = open(path, 'r')
    data = yaml.load(input, pyramid_yaml.PyramidLoader)
    input.close()
    return data

def read_yaml_files (dirpath):
    """Read YAML files, if present, and return their contents."""
    
    index_yml = read_yaml(os.path.join(dirpath, 'index.yml'))
    nav_yml = read_yaml(os.path.join(dirpath, 'nav.yml'))

    return index_yml, nav_yml

