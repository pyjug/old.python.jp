#!/usr/bin/env python
"""Show the UTC date and time in the format useful for newsindex.yml.
"""

import datetime

print datetime.datetime.utcnow().strftime('%a, %d %B %Y, %I:%M +0000')
