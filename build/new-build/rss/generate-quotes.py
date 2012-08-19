#!/usr/bin/python
# -*- encoding: iso-8859-1 -*-

# Assemble an RSS feed of quotations about Python
# Currently this feed needs to be manually copied into the data tree.
#
# Omissions:
#  * no date/time or GUID on items.
#  * could add category tags
#


import sys
sys.path.append('..')

import re
import datetime, PyRSS2Gen
import rst_html

rss = PyRSS2Gen.RSS2(title="Quotes about Python",
                     link="http://www.python.org/about/quotes/",
                     description="""Python is used successfully in
thousands of real-world business 
applications around the world, including many large and mission
critical systems.  Here are some quotes from happy Python users.""",
lastBuildDate = datetime.datetime.now())

def add (title, body):
    html = rst_html.process_rst('quotes', body)
    html = re.sub('<!--.*?--><!--.*?-->', '', html)
    html = html.strip()
    item = PyRSS2Gen.RSSItem(title=title, 
                             description=html)
    rss.items.append(item)

add("YouTube.com", """
"Python is fast enough for our site and allows us to produce
maintainable features in record times, with a minimum of developers,"
said Cuong Do, Software Architect, `YouTube.com
<http://youtube.com>`_.""")


add("Industrial Light & Magic", """
"Python plays a key role in our production pipeline.  Without it a
project the size of Star Wars: Episode II would have been very
difficult to pull off. From crowd rendering to batch processing to
compositing, Python binds all things together," said Tommy Burnette,
Senior Technical Director, `Industrial Light & Magic <http://www.ilm.com>`_.
""")

add("Industrial Light & Magic", """
"Python is everywhere at ILM. It's used to extend the capabilities
of our applications, as well as providing the glue between them. Every
CG image we create has involved Python somewhere in the process," said
Philip Peterson, Principal Engineer, Research & Development, `Industrial Light & Magic <http://www.ilm.com>`_.
""")

add("Google", """
"Python has been an important part of Google since the beginning,
and remains so as the system grows and evolves. Today dozens of Google
engineers use Python, and we're looking for more people with skills in
this language." said Peter Norvig, Director of Research at `Google <http://google.com>`_.
""")

add("Journyx", """
"Journyx technology, from the source code of our software to the code that
maintains our Web site and ASP sites, is entirely based on Python. It
increases our speed of development and keeps us several steps ahead of
competitors while remaining easy to read and use.  It's as high level of a
language as you can have without running into functionality problems.  I
estimate that Python makes our coders 10 times more productive than Java
programmers, and 100 times more than C programmers." -- Curt Finch, CEO,
`Journyx <http://www.journyx.com>`_
""")

add("IronPort", """
"IronPort email gateway appliances are used by the largest
corporations and ISPs in the world," said Mark Peek, Sr. Director of
Engineering at `IronPort Systems <http://www.ironport.com>`_.  "Python
is a critical ingredient in this high performance system. IronPort's
suite of products contains over a million lines of Python. The PSF is
an invaluable resource that helps keep Python on the cutting edge."
""")

add("EVE Online", """
"Python enabled us to create `EVE Online <http://www.eve-online.com/>`_, 
a massive multiplayer game, in record
time. The EVE Online server cluster runs over 25,000 simultaneous
players in a shared space simulation, most of which is created in
Python. The flexibilities of Python have enabled us to quickly improve
the game experience based on player feedback," said
Hilmar Veigar Petursson of `CCP Games <http://www.ccpgames.com/>`_.
""")

add("HomeGain", """
"HomeGain maintains its commitment to continual improvement through
rapid turnaround of new features and enhancements.  Python supports
this short time-to-market philosophy with concise, clear syntax and a
powerful standard library.  New development proceeds rapidly, and
maintenance of existing code is straightforward and fast," said Geoff
Gerrietts, Software Engineer, `HomeGain.com <http://HomeGain.com>`_.
""")

add("Thawte Consulting", 
"""
"Python makes us extremely productive, and makes
maintaining a large and rapidly evolving codebase relatively
simple," said Mark Shuttleworth.
""")

add("University of Maryland", """
"I have the students learn Python in our undergraduate and graduate
Semantic Web courses.  Why?  Because basically there's nothing else
with the flexibility and as many web libraries," said Prof. James
A. Hendler.
""")

add("EZTrip.com", """

"The travel industry is made up of a myriad supplier data feeds all of
which are proprietary in some way and are constantly changing.   Python
repeatedly has allowed us to access, build and test our in-house
communications with hundreds of travel suppliers around the world in a
matter of days rather then the months it would have taken using other
languages.  Since adopting Python 2 years ago, Python has provided us
with a measurable productivity gain that allows us to stay competitive
in the online travel space," said Michael Engelhart, CTO of
`EZTrip.com <http://www.eztrip.com>`_.
""")

add('RealEstateAgent.com', """
"Python in conjunction with PHP has repeatedly allowed us to develop
fast and proficient applications that permit `Real Estate Agent .com
<http://www.realestateagent.com>`_ to operate with minimal
resources. Python is a critical part of our dynamically growing
cluster directory of real estate agents." said Gadi Hus, Webmaster,
`Volico Web Consulting <http://www.volico.com/>`_
""")

add("Firaxis Games", """
"Like XML, scripting was extremely useful as both a mod tool and an
internal development tool.  If you don't have any need to expose code
and algorithms in a simple and safe way to others, you can argue that
providing a scripting language is not worth the effort.  However, if
you do have that need, as we did, scripting is a no brainer, and it
makes complete sense to use a powerful, documented, cross-platform
standard such as Python."  -- Mustafa Thamer of Firaxis Games, talking
about Civilization IV.  Quoted on page 18 of the August 2005 
`Game Developer Magazine <http://www.gdmag.com/>`_.
""")

add("Firaxis Games", """
"Python, like many good technologies, soon spreads virally throughout
your development team and finds its way into all sorts of applications
and tools.  In other words, Python begins to feel like a big hammer and
coding tasks look like nails."
-- Mustafa Thamer of Firaxis Games, talking about Civilization IV.
Quoted on page 18 of the August 2005 `Game Developer Magazine <http://www.gdmag.com/>`_.
""")

add("Firaxis Games", """
"We chose to use python because we wanted a well-supported scripting
language that could extend our core code. Indeed, we wrote much more
code in python than we were expecting, including all in-game screens
and the main interface. It was a huge win for the project because
writing code in a language with garbage collection simply goes faster
than writing code in C++. The fact that users will be able to easily
mod the interface is a nice plus as well. The downside of python was
that it significantly increased our build times, mostly from linking
with Boost."

-- Soren Johnson, lead designer, Civilization IV.  Quoted 
in `a Slashdot interview <http://games.slashdot.org/games/05/10/27/059220.shtml?tid=206&tid=11>`__.
""")

add("Ubuntu Linux", """
Ubuntu prefers the community to contribute work in Python. We develop
our own tools and scripts in Python and it's much easier for us to
integrate your work if you use the same platform.

-- The Ubuntu Linux developers, from `their list of programming bounties <http://www.ubuntu.com/community/developerzone/bounties>`__.
""")

add("Pardus Linux", u"""
Among the high level languages, Python seemed to be the best choice,
since we already use it in many places like package build scripts,
package manager, control panel modules, and installer program
YALI2. Python has small and has clean source codes. Standard library
is full of useful modules. Learning curve is easy, most of the
developers in our team picked up the language in a few days without
prior experience.

-- Pardus Linux developers Gürer Özen and Görkem Çetin, in `"Speeding Up Linux: One Step Further With Pardus" <http://www.pardus.org.tr/eng/projeler/comar/SpeedingUpLinuxWithPardus.html>`__.
""")

add("ITA Software", """
We knew we needed a software load balancer to meet a customer commitment to have their site up and running.

We had this hacked-together version that somebody had written in Perl
in a week, but it fell over continuously. And we needed something that
we could put together that would replace it but that also would be
maintainable over the long run.

Since then, we've changed how we use Python a ton internally.
We have lots more production software written in Python. We've
basically reimplemented all our production service monitoring in
Python and also our production software management infrastructure for
a significant amount of what we run.

-- Dan Kelley, director of application integration at ITA Software,
quoted in `eWeek <http://www.eweek.com/article2/0,1895,2100629,00.asp>`__.
""")

add("ITA Software", """
Since then, we've changed how we use Python a ton internally. We have
lots more production software written in Python. We've basically
reimplemented all our production service monitoring in Python and also
our production software management infrastructure for a significant
amount of what we run.

A big component to that has been our use of Twisted Python. We're
pretty reliant on the Twisted framework, and we use it for our
base-line management software that we use to run the great majority of
production services that we have, our monitoring infrastructure and
the next-generation thing that we have coming, which is a suite of
programs that will automate the upgrade process for us.

-- Dan Kelley, director of application integration at ITA Software,
quoted in `eWeek <http://www.eweek.com/article2/0,1895,2100629,00.asp>`__.
""")

add("ITA Software", """

There are two critical components that are written in Python, without
which the system couldn't exist, Kelley said. The first is the
inventory controller, which keeps track of what seats are available on
what planes.

However,"we think of the most core [component] as the piece that takes reservation requests and records them in a database," Kelley said. "That's written in LISP. But the next most critical thing is the thing that's maintaining inventory levels on airplanes, and that's written in Python." 

-- From `"Python Slithers Into Systems" <http://www.eweek.com/article2/0,1895,2100629,00.asp>`__ in eWeek.
""")

add("ITA Software", """

Historically, [Python] is not known for being something that somebody
would go out and code enterprise software in.  [However,] it's definitely an enterprise-caliber language in terms of stability, scalability [and] the ability to have a large number of people work together on a project.

-- Dan Kelley, director of application integration at ITA Software,
quoted in `eWeek <http://www.eweek.com/article2/0,1895,2100629,00.asp>`__.
""")

add("ITA Software", """

We have a wonderful ability here to choose the right tool for the
job. We have components that are written in Java, in C++, in Python,
and Ruby and Perl. [Python is] definitely viewed internally here by
some of the best computer scientists in the world, people from MIT's
AI [artificial intelligence] and CS [computer science] labs, as
enterprise worthy.

-- Dan Kelley, director of application integration at ITA Software,
quoted in `eWeek <http://www.eweek.com/article2/0,1895,2100629,00.asp>`__.
""")

add("Washington Post", """

Personally, I have direct experience using Python as my primary
development language daily at my day job at Washingtonpost.com. It's a fantastic language that I couldn't live without.

-- Adrian Holovaty, quoted in `eWeek <http://www.eweek.com/article2/0,1895,2100629,00.asp>`__.
""")

rss.write_xml(sys.stdout, encoding='utf-8')

