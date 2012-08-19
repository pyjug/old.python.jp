#!/usr/bin/python

# Assemble an RSS feed of success stories about Python
# Currently this feed needs to be manually copied into the data tree.
#
# Omissions:
#  * no date/time or GUID on items.
#  * could add category tags
#


import sys
sys.path.append('..')

import datetime, PyRSS2Gen
import rst_html

rss = PyRSS2Gen.RSS2(title="Python Success Stories",
                     link="http://www.python.org/about/success/",
                     description="""
Python is part of the winning formula for productivity, software quality,
and maintainability at many companies and institutions around the world.
Here are real-life Python success stories, classified by application domain.

If you have a story to tell, please consider
<a href="http://pythonology.org/successguide/">contributing to the collection</a>.
""",
lastBuildDate = datetime.datetime.now())

def add (url, title, body, categories=[]):
    html = rst_html.process_rst('success', body)
    item = PyRSS2Gen.RSSItem(title=title, 
                             description=html)
    for cat in categories:
        item.categories.append(cat)
    
    rss.items.append(item)

add('http://www.python.org/about/success/bats/',
    "Python in The Blind Audio Tactile Mapping System",
    """
The Blind Audio Tactile Mapping System (BATS) seeks to provide access
to maps for the blind and visually impaired. Our goal is to devise ways
to present traditionally visual information to the user's other senses.    
    """,
    ['accessibility', 'assistive',
     'windows', 'user interface', 'gis', 'mapping',
     'postsecondary', 'scientific',
     ]
     )

add('http://www.python.org/about/success/ezro/',
    'Python and Zope in the EZRO Content Management System',
    """
devIS `EZ Reusable Objects (EZRO)`__ is a content management system which can be
used for many different kinds of websites, including traditional information
presentation sites such as http://www.devis.com/, portals like
http://www.milspouse.org/, training sites like http://cable.devis.com/, and
coach style sites.  A coaching site appears as a frame on the edge
of the screen and drives another site in order to walk the user through that
site, as in http://www.careeronestopcoach.org/.
    """,
    ['accessibility', 'scalability', 'web', 'web 2.0',
     'aviation', 'content management',
     'knowledge management', 'administration'
     ])

rss.write_xml(sys.stdout)

