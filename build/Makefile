# This makefile is to build a local copy for testing/troubleshooting .. 
# See server-build.py nd post-commit-svnup.py for what will happen on the server
#
# You can specify what Python interpreter to use by running
#   ``make PYTHON=_interp_``.
PYTHON = python

jobrss: data/community/jobs/content.ht
	mkdir -p out/community/jobs
	$(PYTHON) data/community/jobs/jobs2rss.py  data/community/jobs/ out/community/jobs
	@echo job.rss done

new:
	$(PYTHON) new-build/build.py --cache=pydotorg.cache -v -d data -o out -r images,styles,files,js
	cp out/news/rdf/index.html out/channews.rdf

all: new

quotes:
	cd new-build/rss ; $(PYTHON) generate-quotes.py \
		> ../../data/about/quotes/quotes.rss
	@echo 'You can commit the updated RSS file now.'

start serve:
	$(PYTHON) new-build/run-server.py --fork

stop:
	$(PYTHON) new-build/run-server.py --stop

clean:
	rm  -f pydotorg.cache
	rm -fr out/*

build-all: 
	pyramid -C -d data -o out -r images,styles,files,js

rss: jobrss
	cd new-build/rss; $(PYTHON) read-feeds.py

############################################################
# Server targets:

delcache:
	rm  -f /data/tmp/pydotorg.cache

queue:
	echo "MANUAL" > status/buildqueued

.PHONY: serve quotes clean new all build-all rss delcache queue-build
