#!/usr/bin/python
# Poll for packages that people desire to be ported to Python 3.

import cgi, os, psycopg2, sys, urllib2, re 
import binascii, Cookie, datetime, json
#import cgitb;cgitb.enable()

limit = 25

conn = psycopg2.connect(database="poll3k", user="poll3k")
c = conn.cursor()

def results_json():
    c.execute("select pkg, count(*) from poll3k group by pkg")
    result = {}
    for pkg, count in c.fetchall():
        result[pkg.strip()] = int(count)
    print "Content-Type: text/json"
    print
    print json.dumps(result)

def results(msg="", cookie=None):
    if msg:
        msg = "<em>"+msg+"</em>"
    c.execute("select pkg, count(*) from poll3k group by pkg "
              "order by count(*) desc limit %d" % limit)
    top = []
    for pkg, count in c.fetchall():
        top.append("<tr><td><a href='http://pypi.python.org/pypi/%s'>%s</a></td><td>%s</td></tr>" % (pkg, pkg, count))
    top = "\n".join(top)
    res = """
<html>
<head>
<title>Poll results</title>
</head>
<body>
%s
<p>Here are the %d most often nominated packages
where users desire Python 3 support</p>
<table>
<tr><th>Package</th><th>Number of Votes</th></tr>
%s
</table>
<p>What does this poll mean?</p>
<p>Off-hand, nothing: nominating a package will not
mean that its authors now start porting it to Python 3.</p>
<p>However, we still hope that this still has some effect
on the Python community:</p>
<ul>
<li>Volunteers trying to help now see where help is most
wanted</li>
<li>Package authors now see that there really is (or is
not) demand for getting their package ported.</li>
</ul>
<p>Some packages listed here may already have been ported to Python
3. Please ask the package authors to use the Trove classifier
"Programming Language :: Python :: 3" to indicate that the port has
been done. If you are a package author who doesn't want to use that
classifier for some reason, please contact pydotorg-www at
python.org to get your package unlisted.</p>

<p>Disclaimer: the poll is mostly anonymous, except that we try to
prevent malicious users from ballot-stuffing.  We will not publish
identity information that we have collected. If we suspect massive
ballot stuffing, we might adjust the accounts.</p>

<a href="/">Back to python.org</a>
</body>
</html>
"""
    res = res % (msg, limit, top)
    print "Content-type: text/html"
    if cookie:
        expires = (datetime.datetime.utcnow() + datetime.timedelta(days=60)).strftime('%a, %d %b %Y %H:%M:%S')
        print "Set-Cookie: user=%s; path=/3kpoll; expires=%s" % (cookie, expires)
    print
    print res

def error(msg):
    print "Content-type: text/plain"
    print
    print msg
    raise SystemExit

def submit():
    form = cgi.parse()
    if 'pkg' not in form:
        error('Invalid Form')
    pkg = form['pkg'][0]
    try:
        r = urllib2.urlopen('http://pypi.python.org/simple/'+pkg)
    except urllib2.HTTPError, e:
        if e.code == 404:
            error("The package %s does not exist. Please verify the package name" % pkg)
    data = r.read()

    # use normalized package name, in case of misspellings
    pkg = re.search("Links for (.*?)<", data).group(1)

    c.execute('select count(*) from ported where name=%s', (pkg,))
    if c.fetchone()[0] > 0:
        error('%s already supports Python 3; no need to vote for it' % pkg)

    # check cookie
    cookie = Cookie.SimpleCookie(os.environ.get('HTTP_COOKIE'))
    if 'user' in cookie:
        cookie = cookie['user'].value
    else:
        cookie = binascii.hexlify(os.urandom(5))

    # Check ballot stuffing
    ip = os.environ["REMOTE_ADDR"]
    c.execute("select count(*) from poll3k where ip=%s or cookie=%s", (ip,cookie))
    count = c.fetchone()[0]
    if count >= 10:
        error("You cannot nominate more than three packages")
    c.execute("select count(*) from poll3k where pkg=%s and (ip=%s or cookie=%s)", (pkg, ip, cookie))
    if c.fetchone()[0] > 0:
        error("You have already nominated this package")

    # insert user-agent header
    agent = os.environ["HTTP_USER_AGENT"]
    c.execute('select id from agent where name=%s', (agent,))
    agentid = c.fetchone()
    if agentid:
        agentid = agentid[0]
    else:
        c.execute('insert into agent(name) values(%s) returning id', (agent,))
        agentid = c.fetchone()[0]

    # insert ballot
    c.execute("insert into poll3k(pkg, ip, cookie, agent) values(%s, %s, %s, %s)", (pkg, ip, cookie, agentid))
    conn.commit()
    results(msg = "Thanks for voting. You can nominate %s more packages if you want to." % (9-count),
            cookie = cookie)

# Install database schema
if len(sys.argv) == 2 and sys.argv[1] == 'create':
    c.execute("create table agent(id serial, name text unique)")
    c.execute("create table poll3k(pkg char(20), ip char(45), cookie char(10), agent integer, date timestamp default now())")
    c.execute("create table deleted(pkg char(20), ip char(45), cookie char(10), agent integer, date timestamp default now())")
    c.execute("create table ported(name varchar(80) primary key)")
    conn.commit()
    raise SystemExit

if len(sys.argv) == 2 and sys.argv[1] == 'update_trove':
    import xmlrpclib
    s = xmlrpclib.Server('http://pypi.python.org/pypi')
    packages = set(name for name, version in s.browse(['Programming Language :: Python :: 3']))
    for p in packages:
        c.execute('select count(*) from ported where name=%s', (p,))
        if c.fetchone()[0] != 0:
            continue
        c.execute('insert into ported(name) values(%s)', (p,))
        c.execute('insert into deleted(pkg, ip, cookie, agent, date) '
                  'select pkg, ip, cookie, agent, date from poll3k '
                  'where pkg=%s', (p,))
        c.execute('delete from poll3k where pkg=%s', (p,))
        conn.commit()
    raise SystemExit

if os.environ["REQUEST_METHOD"] == "GET":
    if os.environ["QUERY_STRING"] == 'json':
        results_json()
    else:
        results()
else:
    submit()
