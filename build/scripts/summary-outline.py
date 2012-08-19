"""
Writes an outline of the Python-Dev Summary for the given period,
including collecting the appropriate messages from mail.python.org,
grouping them into threads, sorting the threads by number of messages
and inserting the appropriate summary headers and message links.

Summary sections will be sorted in order of message count so that threads
with more messages will be at the top of the summary outline and threads
with fewer messages will be at the bottom. Threads with fewer than five
messages are put into the Skipped Threads section.

This script will output a single file in the current directory named in
the scheme YYYY-MM-DD_YYYY-MM-DD.txt to indicate the days which the
summary is intended to cover. Once this summary outline is filled in with
appropriate summary paragraphs, it may be used as input to the
summary-publish.py script.
"""

import calendar
import codecs
import datetime
import HTMLParser
import optparse
import re
import textwrap
import time
import urllib

content_format = '''\
=============
Announcements
=============

=========
Summaries
=========

%(summaries)s

================
Deferred Threads
================

==================
Previous Summaries
==================

===============
Skipped Threads
===============

%(skipped)s
'''

summary_format = '''\
%(divider)s
%(title)s
%(divider)s

Contributing thread:

- `%(title)s <%(url)s>`__

'''

skipped_format = '''\
- `%(title)s <%(url)s>`__
'''



class Message(object):
    """An object containing information about a mailing list message."""
    def __init__(self, url, title, date):
        self.url = url
        self.title = title
        self.date = date

def get_url_file(url):
    """Opens the url and returns a file-like object.

    Retries up to five times before giving up.
    """
    for _ in xrange(5):
        try:
            return urllib.urlopen(url)
        except IOError:
            time.sleep(5)
    raise


_mailman_url_format = 'http://mail.python.org/pipermail/python-dev/%s-%s/%s'
_url_title_matcher = re.compile(r'<LI><A HREF="(\d+.html)">\[Python-Dev\]([^<]*)')
_date_matcher = re.compile(r'<A[^>]*TITLE[^>]*>[^<]*</A><BR>\s*<I>([^<]*)</I>', re.DOTALL)

def get_messages(year, month, start_day, end_day):
    """Collects messages from mail.python.org within the specified dates.

    Keyword Arguments:

    year, month -- the integer year and month within which messages should
        be collected.

    start_day, end_day -- the integer days of the month marking the first
        and last day (inclusive) from which messages should be collected
    """
    
    # open up the list of messages by date
    start_datetime = datetime.datetime(year, month, start_day).timetuple()
    month_str = time.strftime('%B', start_datetime)
    dates_url = _mailman_url_format % (year, month_str, "date.html")
    dates_html = get_url_file(dates_url).read()

    # process each email in the list
    unescape = HTMLParser.HTMLParser().unescape
    for email_url, email_title in _url_title_matcher.findall(dates_html):
        email_title = unescape(' '.join(email_title.split()))

        # open up the url indicated and determine the date
        email_url = _mailman_url_format % (year, month_str, email_url)
        url_file = get_url_file(email_url)
        email_html = ''
        for next_html in iter(lambda: url_file.read(1024), ''):
            email_html += next_html
            email_date_match = _date_matcher.search(email_html)
            if email_date_match is not None:
                break
        else:
            message = 'no date found in %r: %r'
            raise Exception(message % (email_url, email_html))

        # convert the date string to a datetime object
        email_date_str = email_date_match.group(1)
        email_date_str = email_date_str.replace('CEST ', '')
        email_date_str = email_date_str.replace('CET ', '')
        email_time_tuple = time.mktime(time.strptime(email_date_str))
        email_date = datetime.datetime.fromtimestamp(email_time_tuple)

        # yield a new message if we're within the appropriate time span
        if start_day <= email_date.day <= end_day:
            yield Message(email_url, email_title, email_date)

        # break out if we've passed the end of the time span        
        if email_date.day > end_day:
            break

def write_summary_outline(year, month, start_day, end_day):
    """Generates a Python-Dev Summary outline for the specified dates.

    Keyword Arguments:

    year, month, start_day, end_day -- integers defining the period
        covered by the summary
    """
    
    
    # collect the messages into threads by their titles
    def get_title_characters(message):
        return ''.join(message.title.split())
    thread_dict = {}
    for message in get_messages(year, month, start_day, end_day):
        key = get_title_characters(message)
        thread_dict.setdefault(key, []).append(message)

    # sort the threads by length and date
    def get_len_and_date(thread_title):
        messages = thread_dict[thread_title]
        return -len(messages), messages[0].date
    thread_titles = iter(sorted(thread_dict, key=get_len_and_date))

    # split the threads into summarized threads and skipped threads
    summary_parts = []
    skipped_parts = []
    for thread_title in thread_titles:
        messages = thread_dict[thread_title]
        message_count = len(messages)

        # pick the longest title as the canonical one
        titles = list(message.title for message in messages)
        longest_title = sorted(titles, key=len)[-1]

        # pick the first (earliest) url as the canonical one
        thread_url = messages[0].url

        # format a single summary section
        if message_count >= 5:
            divider = '-' * len(longest_title)
            params = dict(divider=divider, title=longest_title,
                          count=message_count, url=thread_url)
            summary_parts.append(summary_format % params)

        # format a single skipped thread section
        else:
            params = dict(title=longest_title, count=message_count,
                          url=thread_url)
            skipped_parts.append(skipped_format % params)
    
    # write summary outline to output file
    params = dict(year=year, month=month, start=start_day, end=end_day)
    filename = ('%(year)i-%(month)02i-%(start)02i_'
                '%(year)i-%(month)02i-%(end)02i.txt' % params)
    output_file = open(filename, 'w')
    output_file.write(codecs.BOM_UTF8)
    text = content_format % dict(summaries=''.join(summary_parts),
                                 skipped=''.join(skipped_parts))
    output_file.write(text.encode('utf-8'))


if __name__ == "__main__":
    option_parser = optparse.OptionParser(
        usage='%prog YYYY MM (1|2)',
        description=textwrap.dedent('''\
            Writes an initial summary outline based on the messages for the
            time period. Threads with 5 or more messages will be placed in
            the Summaries section. The remaining threads will be placed in
            the Skipped Threads section.'''))
    options, args = option_parser.parse_args()

    # read the command line arguments
    try:
        yyyy_str, mm_str, first_last_str = args
    except ValueError:
        option_parser.error('wrong number of arguments')

    # check year string
    try:
        year = time.strptime(yyyy_str, '%Y')[0]
    except ValueError:
        option_parser.error('invalid year %r' % year_str)

    # check the month string
    try:
        month = time.strptime(mm_str, '%m')[1]
    except ValueError:
        option_parser.error('invalid month name %r' % mm_str)

    # determine start and end days (inclusive)
    if first_last_str == '1':
        start_day = 1
        end_day = 15
    elif first_last_str == '2':
        start_day = 16
        _, end_day = calendar.monthrange(year, month)
    else:
        option_parser.error('last argument must be "1" or "2"')

    # write the summary outline
    write_summary_outline(year, month, start_day, end_day)