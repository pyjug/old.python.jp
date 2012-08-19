#!/usr/bin/env python

import sys
import copy
import cStringIO
from xml.etree import ElementTree as et


FAQ_TITLES = {
    'general': 'General Python FAQ',
    'programming': 'Programming FAQ',
    'library': 'Library and Extension FAQ',
    'extending': 'Extending/Embedding FAQ',
    'windows': 'Windows FAQ',
    'gui': 'GUI Programming FAQ',
    'installed': '"Why is Python Installed on My Computer?" FAQ',
    }

startquote = unichr(0x201c)
endquote = unichr(0x201d)

def parse_link (href):
    if not href.startswith('link:'):
        return 'href', href

    _, typ, target = href.split(':', 3)
    return typ, target

def fix_link (href, category):
    typ, target = parse_link(href)
    if type == 'href':
        pass
    elif typ == 'zone':
        target_art = article[target]
        target_cat = target_art.get('category', '').split()
        if not target_cat:
            print 'Article lacking category:', target
            target_cat = ['general']
            
        if category in target_cat:
            # Link is to an element in the same category
            href = '#' + target
        else:
            # Link is to a different FAQ
            href = "../%s/#%s" % (target_cat[0], target)
            
    elif typ == 'python':
        href = "XXX"
    elif typ == 'svn':
        href = 'http://svn.python.org/view/python/trunk/%s' % target.lstrip('/')
    elif typ == 'pep':
        href = 'http://www.python.org/dev/peps/pep-%04i/' % int(target)
    elif typ == 'c':
        href = "XXX"
    elif typ == 'rfc':
        href = 'http://rfc%i.x42.com' % int(target)
        
    return href

def write_body (body, cat):
    body = copy.deepcopy(body)
    for a in body.getiterator('a'):
        href = a.get('href')
        a.set('href', fix_link(href, cat))
        a.set('class', 'reference')
    for qelem in body.getiterator('q'):
        qelem.tag = "span"
        qelem.text = startquote + (qelem.text or "")
        if len(qelem):
            qelem[-1].tail = (qelem[-1].tail or "") + endquote
        else:
            qelem.text += endquote
                                             
    return body

def write_category (cat):
    html = et.Element('html')
    tree = et.ElementTree(html)
    
    index = article[cat + '-index']
    body = index.find('body')

    # Transform contents of index article's body
    new_body = write_body(body, cat)

    # Add name, ID to links
    for a in new_body.getiterator('a'):
        href = a.get('href', '')
        if not href.startswith('#'):
            continue
        art = article[href[1:]]
        a.set('id', 'id%03i' % art.href_id)
        a.set('name', 'id%03i' % art.href_id)
        
    # Create table of contents.
    h1 = et.SubElement(html, 'h1')
    h1.text = FAQ_TITLES.get(cat, '%s FAQ' % cat.capitalize())
    div = et.SubElement(html, 'div',
                        {'class': 'contents topic',
                         'id': 'contents'
                         })
    div.tail = '\n'
    for c in new_body.getchildren():
        div.append(c)

    # Loop over links in the index
    id_count = 1
    for a in body.getiterator('a'):
        typ, target = parse_link(a.get('href'))
        if typ != 'zone':
            continue

        art = article[target]

        art_body = art.find('body')
        new_body = write_body(art_body, cat)
        div = et.SubElement(html, 'div',
                            {'class':'section', 'id':target})
        div.tail = '\n'
        h3 = et.SubElement(div, 'h3')
        a = et.SubElement(h3, 'a',
                          {'class': 'toc-backref',
                           'href':'#id%03i' % art.href_id,
                           'name':target})
        a.text = art.find('title').text
        for c in new_body.getchildren():
            div.append(c)

    # Generate text output
    outf = cStringIO.StringIO()
    tree.write(outf)

    # Remove <html>...</html>
    output = outf.getvalue()
    output = output.replace('<html>', '')
    output = output.replace('</html>', '')

    # Write to file
    outf = open('../data/doc/faq/%s/content.ht' % cat, 'w')
    outf.write('Title: XXX unused title\n')
    outf.write('\n')
    outf.write(output)
    outf.close()
    
def main ():
    global article
    tree = et.parse('pyfaq.xml')

    # Make dictionary mapping article names to node.
    article = {}
    for art in tree.getiterator('article'):
        key = art.get('name')
        if key:
            article[key] = art
        
    # Make list of categories to write indexes for.
    categories = [name.replace('-index', '') for name in article
                  if name.endswith('-index')]
    for dummy in ['garbage', 'old', 'comments', 'cleanup']:
        if dummy in categories:
            categories.remove(dummy)

    # Fill in an HREF ID on all the articles
    id_count = 1
    for a in article.values():
        a.href_id = id_count ; id_count += 1

    for cat in categories:
        write_category(cat)

if __name__ == '__main__':
    main()
    
