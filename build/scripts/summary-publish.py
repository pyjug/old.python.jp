"""
Publishes a summary to the webpage and email lists. This involves:

* Augmenting the basic summary content with the appropriate headers and
  footers, including information on how to reach the author

* Creating the appropriate files and directories so that the summary will
  show up on python.org

* Checking the summary for ReST errors

* Mailing out the summary to python-list and python-announce-list after
  the new files are committed to the repository and the new summary pages
  appear on python.org.
"""

import codecs
import datetime
import docutils.core
import docutils.utils
import docutils.writers
import email
import optparse
import os
import re
import smtplib
import textwrap
import time
import urllib2
import unicodedata

CONTENT_YML_TEXT = """\
--- !fragment
# Type of template to use
template: content.html

# The data to pass to the template
local:
  content:
    breadcrumb: !breadcrumb nav.yml nav
    text: !restfile content.rst
"""

INDEX_YML_TEXT = """\
--- !fragment
template: index.html
# The data to pass to the template
local:
  title: !restfiledata
    file: content.rst
    key: title
  content: !fragment content.yml
"""

CONTENT_RST_TEMPLATE = """\
python-dev Summary for %(start_ISO_date)s through %(end_ISO_date)s
++++++++++++++++++++++++++++++++++++++++++++++++++++

.. contents::

[The HTML version of this Summary is available at
http://www.python.org/dev/summary/%(html_name)s]



%(body_text)s



========
Epilogue
========

This is a summary of traffic on the `python-dev mailing list`_ from
%(start_traditional_date)s through %(end_traditional_date)s.
It is intended to inform the wider Python community of on-going
developments on the list on a semi-monthly basis.  An archive_ of
previous summaries is available online.

An `RSS feed`_ of the titles of the summaries is available.
You can also watch comp.lang.python or comp.lang.python.announce for
new summaries (or through their email gateways of python-list or
python-announce, respectively, as found at http://mail.python.org).

This python-dev summary is %(ordinal)swritten by %(author)s.

To contact me, please send email:

- %(author)s (%(author_email)s)

Do *not* post to comp.lang.python if you wish to reach me.

The `Python Software Foundation`_ is the non-profit organization that
holds the intellectual property for Python.  It also tries to advance
the development and use of Python.  If you find the python-dev Summary
helpful please consider making a donation.  You can make a donation at
http://python.org/psf/donations.html .  Every cent counts so even a
small donation with a credit card, check, or by PayPal helps.


--------------------
Commenting on Topics
--------------------

To comment on anything mentioned here, just post to
`comp.lang.python`_ (or email python-list@python.org which is a
gateway to the newsgroup) with a subject line mentioning what you are
discussing.  All python-dev members are interested in seeing ideas
discussed by the community, so don't hesitate to take a stance on
something.  And if all of this really interests you then get involved
and join `python-dev`_!


-------------------------
How to Read the Summaries
-------------------------

This summary is written using reStructuredText_. Any unfamiliar
punctuation is probably markup for reST_ (otherwise it is probably
regular expression syntax or a typo :); you can safely ignore it.  We
do suggest learning reST, though; it's simple and is accepted for
`PEP markup`_ and can be turned into many different formats like HTML
and LaTeX.

.. _python-dev: http://www.python.org/dev/
.. _python-dev mailing list: http://mail.python.org/mailman/listinfo/python-dev
.. _comp.lang.python: http://groups.google.com/groups?q=comp.lang.python
.. _PEP Markup: http://www.python.org/peps/pep-0012.html

.. _reST:
.. _reStructuredText: http://docutils.sf.net/rst.html
.. _Python Software Foundation: http://python.org/psf/

.. _archive: http://www.python.org/dev/summary/
.. _RSS feed: http://www.python.org/dev/summary/channews.rdf

"""

def get_summary_content(summary_name, body_filename,
                        author, author_email, ordinal=""):
    """Substitute necessary values into CONTENT_HT_TEMPLATE

    The  should be the name of the summary in the format
    

    The body_filename should be the name of the file containing the
    content for the summary's body. This is typically the edited output
    of the summary-outline.py script.


    Keyword Arguments:
    
    summary_name -- The YYYY-MM-DD_YYYY-MM-DD name of the summary

    body_filename -- The name of a file containing the body of the summary,
        e.g. the Announcements, Summaries, Skipped Threads, etc. When
        using the output of the summary-outline script, this is typically
        YYYY-MM-DD_YYYY-MM-DD.txt

    author -- The author of the summary

    author_email -- The email address of the author

    ordinal -- The ordinal number of the summary written (e.g. "2nd")
    """

    # read in the body text
    body_file = codecs.open(body_filename, 'r', 'utf-8')
    try:
        body_text = body_file.read()
    finally:
        body_file.close()
    bom = unicode(codecs.BOM_UTF8, 'utf-8')
    if body_text.startswith(bom):
        body_text = body_text[len(bom):]

    # determine the start and end dates for the summary
    start_date_str, end_date_str = summary_name.split('_')
    start_yymmdd = time.strptime(start_date_str, "%Y-%m-%d")[:3]
    end_yymmdd = time.strptime(end_date_str, "%Y-%m-%d")[:3]
    start_date = datetime.date(*start_yymmdd)
    end_date = datetime.date(*end_yymmdd)

    # convert start and end dates to strings
    start_ISO_date = start_date.strftime("%Y-%m-%d")
    end_ISO_date = end_date.strftime("%Y-%m-%d")
    date_range = '%s_%s' % (start_ISO_date, end_ISO_date)

    # add any necessary text if ordinal is provided
    if ordinal:
        ordinal = 'the %s ' % ordinal

    # mildly obscure author email address
    author_email = author_email.replace('@', ' at ').replace('.', ' dot ')

    # assemble all the values for substitution
    mapping = dict(
        body_text=body_text,
        author=author,
        author_email=author_email,
        ordinal=ordinal,
        start_ISO_date=start_ISO_date,
        end_ISO_date=end_ISO_date,
        start_traditional_date=start_date.strftime("%B %d, %Y"),
        end_traditional_date=end_date.strftime("%B %d, %Y"),
        html_name=date_range,)

    # substitute the values into the content template
    return CONTENT_RST_TEMPLATE % mapping

def write_summary_directory(summary_name, summary_content):
    """Writes the files necessary for the summary to show up on python.org.

    Keyword arguments:

    summary_name -- The YYYY-MM-DD_YYYY-MM-DD name of the summary
    
    summary_content -- The textual content of the summary, typically
        produced by calling get_summary_content() above.
    """

    dirname = os.path.dirname
    path_parts = 'data', 'dev', 'summary', summary_name
    summary_dir = os.path.join(dirname(dirname(__file__)), *path_parts)
    if not os.path.exists(summary_dir):
        os.mkdir(summary_dir)
    for filename, content in [('content.rst', summary_content),
                              ('content.yml', CONTENT_YML_TEXT),
                              ('index.yml', INDEX_YML_TEXT)]:
        filepath = os.path.join(summary_dir, filename)
        fileobj = codecs.open(filepath, 'w', 'utf-8')
        try:
            fileobj.write(content)
        finally:
            fileobj.close()
    return summary_dir

def rest_to_html(summary_dir):
    """Converts the summary from ReST to HTML, potentially raising errors.

    Keyword arguments:

    summary_dir -- The directory containing the python.org files for this
        summary, typically a directory named YYYY-MM-DD_YYYY-MM-DD,
        generated by a call to write_summary_directory() above.
    """
    
    overrides = dict(halt_level=0)
    rst_text = open(os.path.join(summary_dir, 'content.rst')).read()
    writer = docutils.writers.get_writer_class('html')
    return docutils.core.publish_string(rst_text, writer=writer(),
                                        settings_overrides=overrides)

def is_visible_on_python_org(summary_name):
    """Determines if the summary is now visible on python.org.

    Checks once a minute for up to 10 minutes to see if the commits to
    the repository have propogated to the webpage.

    Keyword Arguments:

    summary_name -- The YYYY-MM-DD_YYYY-MM-DD name of the summary
    """
    
    summary_url = 'http://www.python.org/dev/summary/' + summary_name
    for _ in xrange(10):
        try:
            urllib2.urlopen(summary_url)
        except urllib2.HTTPError:
            pass
        else:
            return True
        time.sleep(60)
    return False

_to_addrs = 'python-list@python.org', 'python-announce-list@python.org'
def mail_summary(summary_dir, smtp_host, from_addr, to_addrs=_to_addrs):
    """Mails the summary to the appropriate lists.

    The summary is first converted to plain text, substituting UTF-8
    characters with their closest ASCII equivalents.

    Keyword Arguments:

    summary_dir -- The directory containing the python.org files for this
        summary, typically a directory named YYYY-MM-DD_YYYY-MM-DD,
        generated by a call to write_summary_directory() above.

    smtp_host -- The SMTP host through which the email should be sent

    from_addr -- The email address from which the email should be sent

    to_addrs -- The email addresses to which the email should be sent, by
        default, python-list@python.org and python-announce-list@python.org
    """
    
    # read in the summary text
    rst_file = open(os.path.join(summary_dir, 'content.rst'))
    utf8_text = rst_file.read().decode('utf-8')
    rst_file.close()

    # convert all UTF-8 characters into their closest ASCII equivalent
    ascii_text_chars = []
    for char in utf8_text:
        try:
            char = str(char)
        except UnicodeEncodeError:
            ord_strs = unicodedata.decomposition(char).split()
            char = chr(int(ord_strs[0], 16))
        ascii_text_chars.append(char)
    ascii_text = ''.join(ascii_text_chars)

    # create a message with the appropriate headers
    message = email.message_from_string(ascii_text)
    message['Subject'] = ascii_text.splitlines()[0]
    message['From'] = from_addr
    message['To'] = ', '.join(to_addrs)

    # send the message
    mailer = smtplib.SMTP()
    mailer.connect(smtp_host)
    mailer.sendmail(from_addr, to_addrs, message.as_string())
    mailer.close()


if __name__ == '__main__':
    # set up an option parser for the command line
    option_parser = optparse.OptionParser(
        usage='%prog [options] YYYY-MM-DD_YY-MM-DD.txt',
        description=textwrap.dedent('''\
            Add the header and footer to a ReST-formatted summary and
            create the necessary directory and files for it to show up
            on python.org. The input to this program is a completed summary
            based on the outline generated by the summary-outline.py
            program. You will be prompted as necessary for things like
            fixing ReST errors or committing changes to the Subversion
            repository.'''))
    option_parser.add_option(
        '-a', '--author', default='Steven Bethard',
        help='the author of the summary')
    option_parser.add_option(
        '-e', '--author-email', metavar='EMAIL',
        default='steven.bethard@gmail.com',
        help='the email address of the author of the summary')
    option_parser.add_option(
        '-s', '--smtp-host', metavar='HOST', default='smtp.comcast.net',
        help='the SMTP host through which the email should be sent')
    option_parser.add_option(
        '-o', '--ordinal', metavar='Nth', default='',
        help='the ordinal number of the summary, e.g. "2nd"')
    option_parser.add_option(
        '--rest-only', action='store_true',
        help='only check to see that the text is valid ReST')
    options, args = option_parser.parse_args()

    # extract the filename for the summary body
    try:
        body_filename, = args
    except ValueError:
        option_parser.error('wrong number of arguments')

    # keep trying to generate the summary until there are no longer
    # any ReST errors
    while True:

        # determine the summary content
        summary_name = os.path.basename(body_filename)
        summary_name, _ = os.path.splitext(summary_name)
        summary_content = get_summary_content(
            summary_name,
            body_filename,
            author=options.author,
            author_email=options.author_email,
            ordinal=options.ordinal)

        # generate directory, content.ht, content.yml, index.yml
        summary_dir = write_summary_directory(summary_name, summary_content)

        # if there are no ReST errors, break out
        try:
            html_text = rest_to_html(summary_dir)
        except docutils.utils.ApplicationError, rest_error:
            # if there were ReST errors, ask the user to correct them
            print 'There were ReST errors in the summary file:'
            print rest_error
            print 'Please hit <enter> when they are fixed.'
            raw_input()
        else:
            summary_html_file = open('summary.html', 'w')
            summary_html_file.write(html_text)
            summary_html_file.close()
            print 'Please verify that summary.html looks right.'
            print 'Type just <enter> to accept or anything else to retry.'
            if not raw_input():
                break

    # if we're not just checking the ReST, mail out the summaries
    if not options.rest_only:

        # ask user to commit changes to Subversion
        print 'Please update the links in data/dev/summary/content.ht, '
        print 'svn-add the new directories, commit your changes to '
        print 'Subversion and hit <enter> when done.'
        raw_input()

        # make sure updates are visible online
        while not is_visible_on_python_org(summary_name):
            print 'Summaries are not showing up on python.org.'
            print 'Check that changes have been committed to Subversion '
            print 'and hit <enter> when done.'
            raw_input()

        # send out the emails to comp.lang.python and python-announce
        mail_summary(summary_dir, options.smtp_host, options.author_email)
