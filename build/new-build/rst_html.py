#!/usr/bin/env python
# -*-Python-*-
# 
# Contains the process_rst() function, which turns ReST files into
# HTML output that can be included in a page.
#

import StringIO
from docutils import core, io
from docutils.writers import html4css1

class WeblogWriter (html4css1.Writer):
    def __init__ (self):
        html4css1.Writer.__init__(self)
        self.translator_class = WeblogHTMLTranslator

class WeblogHTMLTranslator (html4css1.HTMLTranslator):
    doctype = ""	
    content_type = "<!--%s-->"
    generator = "<!--%s-->"
    
    def __init__(self, document):
        html4css1.HTMLTranslator.__init__(self, document)
        self.head_prefix = []
        self.body_prefix = []
        self.stylesheet = []
        self.body_suffix = []
        self.section_level = 1
        
    def visit_system_message(self, node):
        pass

    def visit_document (self, node):
        pass
    
    def depart_document (self, node):
        pass

                                            
def process_rst (filename, body):
    "Parse 'body' as RST and convert it to HTML"
    output_file = StringIO.StringIO()
    settings = {
        'input_encoding': 'utf-8',
        'output_encoding': 'utf-8',
        # cloak email addresses to reduce spam
        'cloak_email_addresses': 1,
        # Forbid file inclusion
        'file_insertion_enabled': False,
        # remove reST comments from output HTML: 
        'strip_comments': True,
        }
    body = core.publish_string(
        reader_name='standalone',
        parser_name='restructuredtext',
        writer=WeblogWriter(),
        writer_name='html',
        source_path=filename,
        source=body,
        destination_path=filename,
        settings=None,
	settings_overrides=settings)

    # Return a Unicode string.
    body = unicode(body, 'utf-8')
    return body

