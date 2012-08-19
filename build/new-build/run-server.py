#!/usr/bin/env python

# Port to run on
PORT=8005

# Path to file containing the PID
PID_FILE = 'run-server.pid'

# Script to serve up the contents of the out/ directory.

import os, sys, time
from BaseHTTPServer import *
from SimpleHTTPServer import *

redirects = {}

class CDevNull:
    """Replacement for os.devnull which crashes the server for some reason"""
    def write(*args):
        pass
    
class FixedHTTPRequestHandler(SimpleHTTPRequestHandler):
    def send_head(self):
        """Common code for GET and HEAD commands.

        This sends the response code and MIME headers.

        Return value is either a file object (which has to be copied
        to the outputfile by the caller unless the command was HEAD,
        and must be closed by the caller under all circumstances), or
        None, in which case the caller has nothing further to do.

        """
        path = self.translate_path(self.path)
        if self.path in redirects:
            self.send_response(301)
            self.send_header("Location", redirects[self.path])
            self.end_headers()
            return None
            
        f = None
        if os.path.isdir(path):
            if not self.path.endswith('/'):
                # redirect browser - doing basically what apache does
                self.send_response(301)
                self.send_header("Location", self.path + "/")
                self.end_headers()
                return None
            for index in "index.html", "index.htm":
                index = os.path.join(path, index)
                if os.path.exists(index):
                    path = index
                    break
            else:
                return self.list_directory(path)
        ctype = self.guess_type(path)
        if ctype.startswith('text/'):
            mode = 'r'
        else:
            mode = 'rb'
        try:
            f = open(path, mode)
        except IOError:
            self.send_error(404, "File not found")
            return None
        self.send_response(200)
        self.send_header("Content-type", ctype)
        fs = os.fstat(f.fileno())
        self.send_header("Content-Length", str(fs[6]))
        self.send_header("Last-Modified", self.date_time_string())
        self.end_headers()
        return f

# redirect file removed, comment this out
for x in ():
# Read redirect file
#for line in open('redirects.txt', 'r'):
    # Ignore blank lines
    if line.strip() == '':
        continue

    L = line.split()
    if len(L) != 2:
        print >>sys.stderr, 'Bad line in redirect file: %r' % line
        continue

    old, new = L
    old = old.rstrip('/')
    redirects[old + '/'] = redirects[old] = new
    
    
# Try to kill existing process
try:
    f = open(PID_FILE, 'r')
except:
    print "No existing process"
else:
    pid = int(f.read())
    f.close()
    try:
        os.kill(pid, 15)
        print "Terminated existing process", pid
        time.sleep(0.5)
        os.remove(PID_FILE)
    except:
        print "Failed to kill existing process", pid

if '--stop' in sys.argv:
    sys.exit(0)
    
# Fork if requested
if '--fork' in sys.argv:
    child_pid = os.fork()
    forked = True
else:
    child_pid = os.getpid()
    forked = False

# Record server process id
if child_pid:
    f = open(PID_FILE, 'w')
    f.write(str(child_pid))
    f.close()

# Start server
if child_pid == 0 or not forked:

    # Redirect stdout/err if forked
    print "Running server on port", PORT, "; process id is", os.getpid()
    if forked:
        sys.stdout = sys.stderr = CDevNull()
        
    # Run the server
    os.chdir('out')
    server = HTTPServer(('', PORT), FixedHTTPRequestHandler)
    server.serve_forever()
    

