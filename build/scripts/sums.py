#!/usr/bin/env python2.5

from __future__ import with_statement

import os
import sys
import hashlib

basenames = dict((os.path.basename(filename), filename)
                 for filename in sys.argv[1:])
for basename in sorted(basenames):
    filename = basenames[basename]
    size = os.path.getsize(filename)
    with open(filename) as f:
        md5 = hashlib.md5(f.read()).hexdigest()
    print '  %s  %8d  %s' % (md5, size, basename)
